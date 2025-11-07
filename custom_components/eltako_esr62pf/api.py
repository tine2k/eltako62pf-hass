"""API client for Eltako ESR62PF-IP device."""
import asyncio
import logging
import ssl
import time
from typing import Any, Optional

import aiohttp

from .const import (
    API_TOKEN_TTL,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DEVICE_CACHE_TTL,
    ENDPOINT_DEVICES,
    ENDPOINT_LOGIN,
    ENDPOINT_RELAY,
    MAX_RETRIES,
    RELAY_STATE_OFF,
    RELAY_STATE_ON,
    RETRY_BACKOFF_BASE,
)
from .exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoInvalidDeviceError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


class EltakoAPI:
    """API client for Eltako ESR62PF-IP device."""

    def __init__(
        self,
        ip_address: str,
        pop_credential: str,
        port: int = DEFAULT_PORT,
        verify_ssl: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client.

        Args:
            ip_address: IP address of the Eltako device
            pop_credential: Proof of Possession credential for authentication
            port: Port number (default: 443)
            verify_ssl: Whether to verify SSL certificates (default: True)
            session: Optional aiohttp session to use
            timeout: Request timeout in seconds (default: 10)
        """
        self._ip_address = ip_address
        self._pop_credential = pop_credential
        self._port = port
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._session = session
        self._owns_session = session is None

        # Token management
        self._api_key: Optional[str] = None
        self._token_timestamp: Optional[float] = None
        self._token_lock = asyncio.Lock()

        # Device caching
        self._devices_cache: Optional[list[dict[str, Any]]] = None
        self._devices_cache_timestamp: Optional[float] = None

        # Relay control queueing
        self._relay_lock = asyncio.Lock()

        # SSL context
        self._ssl_context = self._create_ssl_context()

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for HTTPS connections.

        Returns:
            SSL context or None if SSL verification is disabled
        """
        if not self._verify_ssl:
            # Disable SSL verification for self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        return None  # Use default SSL verification

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return f"https://{self._ip_address}:{self._port}"

    def _is_token_expired(self) -> bool:
        """Check if the current API token is expired.

        Returns:
            True if token is expired or not set, False otherwise
        """
        if self._api_key is None or self._token_timestamp is None:
            return True

        elapsed = time.time() - self._token_timestamp
        return elapsed >= API_TOKEN_TTL

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            aiohttp ClientSession
        """
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def async_login(self) -> str:
        """Authenticate with the Eltako device and get API key.

        Returns:
            API key for subsequent requests

        Raises:
            EltakoAuthenticationError: If authentication fails
            EltakoConnectionError: If connection fails
            EltakoTimeoutError: If request times out
        """
        url = f"{self.base_url}{ENDPOINT_LOGIN}"
        payload = {
            "user": DEFAULT_USERNAME,
            "password": self._pop_credential,
        }

        try:
            session = await self._get_session()
            async with session.post(
                url,
                json=payload,
                ssl=self._ssl_context,
            ) as response:
                if response.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    raise EltakoAuthenticationError("Invalid PoP credential")

                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Login failed with status %d: %s",
                        response.status,
                        error_text,
                    )
                    raise EltakoAPIError(
                        f"Login failed with status {response.status}"
                    )

                data = await response.json()
                api_key = data.get("apiKey")

                if not api_key:
                    raise EltakoAPIError("No API key in login response")

                # Cache the token with timestamp
                self._api_key = api_key
                self._token_timestamp = time.time()

                _LOGGER.debug("Successfully authenticated and cached API key")
                return api_key

        except aiohttp.ClientConnectorError as err:
            _LOGGER.error("Connection error during login: %s", err)
            raise EltakoConnectionError(f"Failed to connect to device: {err}") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout during login")
            raise EltakoTimeoutError("Login request timed out") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error during login: %s", err)
            raise EltakoConnectionError(f"HTTP error: {err}") from err

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid, non-expired API token.

        This method checks if the token is expired and refreshes it if needed.
        Uses a lock to prevent concurrent refresh attempts.

        Raises:
            EltakoAuthenticationError: If token refresh fails
        """
        async with self._token_lock:
            if self._is_token_expired():
                _LOGGER.debug("Token expired or not set, refreshing...")
                await self.async_login()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        retry_count: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated API request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            retry_count: Current retry attempt (for internal use)
            **kwargs: Additional arguments to pass to aiohttp request

        Returns:
            JSON response data

        Raises:
            EltakoAuthenticationError: If authentication fails
            EltakoConnectionError: If connection fails
            EltakoAPIError: If API returns an error
            EltakoTimeoutError: If request times out
        """
        # Ensure we have a valid token before making the request
        await self._ensure_valid_token()

        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = self._api_key

        try:
            session = await self._get_session()
            async with session.request(
                method,
                url,
                headers=headers,
                ssl=self._ssl_context,
                **kwargs,
            ) as response:
                # Handle 401 - token expired, refresh and retry once
                if response.status == 401 and retry_count == 0:
                    _LOGGER.debug("Received 401, refreshing token and retrying")
                    async with self._token_lock:
                        await self.async_login()
                    # Retry the request once with new token
                    return await self._make_request(
                        method, endpoint, retry_count=retry_count + 1, **kwargs
                    )

                if response.status not in (200, 201, 204):
                    error_text = await response.text()
                    _LOGGER.error(
                        "API request failed with status %d: %s",
                        response.status,
                        error_text,
                    )
                    raise EltakoAPIError(
                        f"API request failed with status {response.status}"
                    )

                # Handle empty responses (e.g., 204 No Content)
                if response.status == 204:
                    return {}

                return await response.json()

        except aiohttp.ClientConnectorError as err:
            # Implement exponential backoff retry for connection errors
            if retry_count < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_BASE ** retry_count
                _LOGGER.warning(
                    "Connection error (attempt %d/%d), retrying in %ds: %s",
                    retry_count + 1,
                    MAX_RETRIES,
                    wait_time,
                    err,
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method, endpoint, retry_count=retry_count + 1, **kwargs
                )

            _LOGGER.error(
                "Connection error after %d retries: %s", MAX_RETRIES, err
            )
            raise EltakoConnectionError(
                f"Failed to connect after {MAX_RETRIES} retries"
            ) from err

        except asyncio.TimeoutError as err:
            # Implement exponential backoff retry for timeouts
            if retry_count < MAX_RETRIES:
                wait_time = RETRY_BACKOFF_BASE ** retry_count
                _LOGGER.warning(
                    "Timeout (attempt %d/%d), retrying in %ds",
                    retry_count + 1,
                    MAX_RETRIES,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                return await self._make_request(
                    method, endpoint, retry_count=retry_count + 1, **kwargs
                )

            _LOGGER.error("Request timed out after %d retries", MAX_RETRIES)
            raise EltakoTimeoutError(
                f"Request timed out after {MAX_RETRIES} retries"
            ) from err

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP error: %s", err)
            raise EltakoConnectionError(f"HTTP error: {err}") from err

    def _is_device_cache_expired(self) -> bool:
        """Check if the device cache is expired.

        Returns:
            True if cache is expired or not set, False otherwise
        """
        if self._devices_cache is None or self._devices_cache_timestamp is None:
            return True

        elapsed = time.time() - self._devices_cache_timestamp
        return elapsed >= DEVICE_CACHE_TTL

    async def async_get_devices(
        self, force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Get list of devices from the Eltako API.

        Args:
            force_refresh: Force refresh cache even if not expired

        Returns:
            List of device dictionaries containing GUIDs and metadata

        Raises:
            EltakoAuthenticationError: If authentication fails
            EltakoConnectionError: If connection fails
            EltakoAPIError: If API returns an error
            EltakoTimeoutError: If request times out
        """
        # Return cached devices if available and not expired
        if not force_refresh and not self._is_device_cache_expired():
            _LOGGER.debug("Returning cached device list")
            return self._devices_cache

        _LOGGER.debug("Fetching device list from API")
        response = await self._make_request("GET", ENDPOINT_DEVICES)

        # Extract devices from response
        devices = response.get("devices", [])
        if not isinstance(devices, list):
            _LOGGER.error("Invalid devices response format: expected list")
            raise EltakoAPIError("Invalid devices response format")

        # Cache the devices with timestamp
        self._devices_cache = devices
        self._devices_cache_timestamp = time.time()

        _LOGGER.debug("Successfully fetched and cached %d devices", len(devices))
        return devices

    async def async_set_relay(self, device_guid: str, state: str) -> None:
        """Set relay state for a device.

        Args:
            device_guid: GUID of the device to control
            state: Relay state ('on' or 'off')

        Raises:
            EltakoInvalidDeviceError: If device GUID is invalid
            EltakoAuthenticationError: If authentication fails
            EltakoConnectionError: If connection fails
            EltakoAPIError: If API returns an error
            EltakoTimeoutError: If request times out
        """
        # Validate device GUID
        if not device_guid or not isinstance(device_guid, str):
            raise EltakoInvalidDeviceError("Device GUID must be a non-empty string")

        # Validate state
        if state not in (RELAY_STATE_ON, RELAY_STATE_OFF):
            raise EltakoAPIError(
                f"Invalid relay state: {state}. Must be '{RELAY_STATE_ON}' or '{RELAY_STATE_OFF}'"
            )

        # Queue relay commands to prevent race conditions
        async with self._relay_lock:
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            payload = {"value": state}

            _LOGGER.debug("Setting relay %s to %s", device_guid, state)
            await self._make_request("PUT", endpoint, json=payload)
            _LOGGER.debug("Successfully set relay %s to %s", device_guid, state)

    async def async_close(self) -> None:
        """Close the API client and cleanup resources."""
        if self._session and self._owns_session:
            await self._session.close()
            self._session = None
        _LOGGER.debug("API client closed")

    async def __aenter__(self) -> "EltakoAPI":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.async_close()
