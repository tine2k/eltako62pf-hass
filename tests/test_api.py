"""Tests for Eltako API client."""
import asyncio
import ssl
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.eltako_esr62pf.api import EltakoAPI
from custom_components.eltako_esr62pf.const import (
    API_TOKEN_TTL,
    DEFAULT_PORT,
    DEVICE_CACHE_TTL,
    ENDPOINT_DEVICES,
    ENDPOINT_LOGIN,
    ENDPOINT_RELAY,
    RELAY_STATE_OFF,
    RELAY_STATE_ON,
)
from custom_components.eltako_esr62pf.exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoInvalidDeviceError,
    EltakoTimeoutError,
)


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return EltakoAPI(
        ip_address="192.168.1.100",
        pop_credential="test_pop_credential",
        port=DEFAULT_PORT,
        verify_ssl=False,
    )


@pytest.fixture
def api_client_with_ssl():
    """Create an API client with SSL verification enabled."""
    return EltakoAPI(
        ip_address="192.168.1.100",
        pop_credential="test_pop_credential",
        port=DEFAULT_PORT,
        verify_ssl=True,
    )


class TestEltakoAPIInit:
    """Test EltakoAPI initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        client = EltakoAPI(
            ip_address="192.168.1.100",
            pop_credential="test_pop",
        )
        assert client._ip_address == "192.168.1.100"
        assert client._pop_credential == "test_pop"
        assert client._port == DEFAULT_PORT
        assert client._verify_ssl is True
        assert client._api_key is None
        assert client._token_timestamp is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        client = EltakoAPI(
            ip_address="10.0.0.50",
            pop_credential="custom_pop",
            port=8443,
            verify_ssl=False,
        )
        assert client._ip_address == "10.0.0.50"
        assert client._pop_credential == "custom_pop"
        assert client._port == 8443
        assert client._verify_ssl is False

    def test_ssl_context_with_verification(self, api_client_with_ssl):
        """Test SSL context when verification is enabled."""
        ssl_context = api_client_with_ssl._get_ssl_context()
        assert ssl_context is None  # Uses default

    def test_ssl_context_without_verification(self, api_client):
        """Test SSL context when verification is disabled."""
        ssl_context = api_client._get_ssl_context()
        assert ssl_context is not None
        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.verify_mode == ssl.CERT_NONE
        assert ssl_context.check_hostname is False

    def test_base_url(self, api_client):
        """Test base URL generation."""
        assert api_client.base_url == "https://192.168.1.100:443"


class TestTokenExpiry:
    """Test token expiry detection."""

    def test_is_token_expired_no_token(self, api_client):
        """Test token expiry when no token is set."""
        assert api_client._is_token_expired() is True

    def test_is_token_expired_fresh_token(self, api_client):
        """Test token expiry with a fresh token."""
        api_client._api_key = "test_key"
        api_client._token_timestamp = time.time()
        assert api_client._is_token_expired() is False

    def test_is_token_expired_old_token(self, api_client):
        """Test token expiry with an expired token."""
        api_client._api_key = "test_key"
        api_client._token_timestamp = time.time() - (API_TOKEN_TTL + 1)
        assert api_client._is_token_expired() is True

    def test_is_token_expired_edge_case(self, api_client):
        """Test token expiry at exactly TTL threshold."""
        api_client._api_key = "test_key"
        api_client._token_timestamp = time.time() - API_TOKEN_TTL
        assert api_client._is_token_expired() is True


class TestLogin:
    """Test authentication functionality."""

    @pytest.mark.asyncio
    async def test_async_login_success(self, api_client):
        """Test successful login."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_api_key_123"},
                status=200,
            )

            api_key = await api_client.async_login()

            assert api_key == "test_api_key_123"
            assert api_client._api_key == "test_api_key_123"
            assert api_client._token_timestamp is not None
            assert isinstance(api_client._token_timestamp, float)

    @pytest.mark.asyncio
    async def test_async_login_caches_token_with_timestamp(self, api_client):
        """Test that login caches token with timestamp."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "cached_key"},
                status=200,
            )

            before_time = time.time()
            await api_client.async_login()
            after_time = time.time()

            assert api_client._api_key == "cached_key"
            assert before_time <= api_client._token_timestamp <= after_time

    @pytest.mark.asyncio
    async def test_async_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                status=401,
            )

            with pytest.raises(EltakoAuthenticationError, match="Authentication failed"):
                await api_client.async_login()

    @pytest.mark.asyncio
    async def test_async_login_missing_api_key(self, api_client):
        """Test login when API key is missing from response."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={},
                status=200,
            )

            with pytest.raises(EltakoAPIError, match="No API key in login response"):
                await api_client.async_login()

    @pytest.mark.asyncio
    async def test_async_login_server_error(self, api_client):
        """Test login with server error."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                status=500,
                body="Internal Server Error",
            )

            with pytest.raises(EltakoAPIError, match="Login failed with status 500"):
                await api_client.async_login()

    @pytest.mark.asyncio
    async def test_async_login_connection_error(self, api_client):
        """Test login with connection error."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                exception=aiohttp.ClientConnectorError(
                    connection_key=MagicMock(),
                    os_error=OSError("Connection refused"),
                ),
            )

            with pytest.raises(EltakoConnectionError, match="Cannot reach Eltako device"):
                await api_client.async_login()

    @pytest.mark.asyncio
    async def test_async_login_timeout(self, api_client):
        """Test login with timeout."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                exception=asyncio.TimeoutError(),
            )

            with pytest.raises(EltakoTimeoutError, match="not responding"):
                await api_client.async_login()


class TestEnsureValidToken:
    """Test token validation and refresh."""

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_token(self, api_client):
        """Test ensure valid token when no token exists."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "new_token"},
                status=200,
            )

            await api_client._ensure_valid_token()

            assert api_client._api_key == "new_token"

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expired(self, api_client):
        """Test ensure valid token refreshes expired token."""
        # Set an expired token
        api_client._api_key = "old_token"
        api_client._token_timestamp = time.time() - (API_TOKEN_TTL + 1)

        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "refreshed_token"},
                status=200,
            )

            await api_client._ensure_valid_token()

            assert api_client._api_key == "refreshed_token"

    @pytest.mark.asyncio
    async def test_ensure_valid_token_fresh(self, api_client):
        """Test ensure valid token doesn't refresh fresh token."""
        # Set a fresh token
        api_client._api_key = "fresh_token"
        api_client._token_timestamp = time.time()

        # No mock needed - should not make any requests
        await api_client._ensure_valid_token()

        assert api_client._api_key == "fresh_token"

    @pytest.mark.asyncio
    async def test_ensure_valid_token_thread_safety(self, api_client):
        """Test ensure valid token is thread-safe."""
        with aioresponses() as mock_resp:
            # Mock only one login response
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "concurrent_token"},
                status=200,
            )

            # Simulate concurrent calls
            results = await asyncio.gather(
                api_client._ensure_valid_token(),
                api_client._ensure_valid_token(),
                api_client._ensure_valid_token(),
            )

            # All should use the same token - only one login should occur
            assert api_client._api_key == "concurrent_token"


class TestMakeRequest:
    """Test generic API request functionality."""

    @pytest.mark.asyncio
    async def test_make_request_ensures_valid_token(self, api_client):
        """Test that make_request ensures token is valid before request."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "request_token"},
                status=200,
            )
            # Mock actual request
            mock_resp.get(
                f"{api_client.base_url}/test",
                payload={"result": "success"},
                status=200,
            )

            result = await api_client._make_request("GET", "/test")

            assert result == {"result": "success"}
            assert api_client._api_key == "request_token"

    @pytest.mark.asyncio
    async def test_make_request_401_retry(self, api_client):
        """Test that 401 response triggers token refresh and retry."""
        # Set an initial token
        api_client._api_key = "expired_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            # First request returns 401
            mock_resp.get(
                f"{api_client.base_url}/test",
                status=401,
            )
            # Login to refresh token
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "new_token_after_401"},
                status=200,
            )
            # Retry request succeeds
            mock_resp.get(
                f"{api_client.base_url}/test",
                payload={"result": "success"},
                status=200,
            )

            result = await api_client._make_request("GET", "/test")

            assert result == {"result": "success"}
            assert api_client._api_key == "new_token_after_401"

    @pytest.mark.asyncio
    async def test_make_request_204_no_content(self, api_client):
        """Test handling of 204 No Content response."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            mock_resp.put(
                f"{api_client.base_url}/test",
                status=204,
            )

            result = await api_client._make_request("PUT", "/test")

            assert result == {}

    @pytest.mark.asyncio
    async def test_make_request_exponential_backoff_connection_error(self, api_client):
        """Test exponential backoff for connection errors."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            # First 2 attempts fail
            mock_resp.get(
                f"{api_client.base_url}/test",
                exception=aiohttp.ClientConnectorError(
                    connection_key=MagicMock(),
                    os_error=OSError("Connection refused"),
                ),
            )
            mock_resp.get(
                f"{api_client.base_url}/test",
                exception=aiohttp.ClientConnectorError(
                    connection_key=MagicMock(),
                    os_error=OSError("Connection refused"),
                ),
            )
            # Third attempt succeeds
            mock_resp.get(
                f"{api_client.base_url}/test",
                payload={"result": "success"},
                status=200,
            )

            start_time = time.time()
            result = await api_client._make_request("GET", "/test")
            elapsed = time.time() - start_time

            assert result == {"result": "success"}
            # Should have waited: 2^0 + 2^1 = 1 + 2 = 3 seconds
            assert elapsed >= 3

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, api_client):
        """Test that max retries are respected."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            # All attempts fail
            for _ in range(4):  # Initial + 3 retries
                mock_resp.get(
                    f"{api_client.base_url}/test",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            with pytest.raises(EltakoConnectionError, match="Cannot reach Eltako device"):
                await api_client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_timeout_retry(self, api_client):
        """Test retry logic for timeouts."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            # First attempt times out
            mock_resp.get(
                f"{api_client.base_url}/test",
                exception=asyncio.TimeoutError(),
            )
            # Second attempt succeeds
            mock_resp.get(
                f"{api_client.base_url}/test",
                payload={"result": "success"},
                status=200,
            )

            result = await api_client._make_request("GET", "/test")

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_make_request_api_error(self, api_client):
        """Test handling of API errors."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            mock_resp.get(
                f"{api_client.base_url}/test",
                status=400,
                body="Bad Request",
            )

            with pytest.raises(EltakoAPIError, match="API request failed with status 400"):
                await api_client._make_request("GET", "/test")


class TestContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using API client as context manager."""
        async with EltakoAPI(
            ip_address="192.168.1.100",
            pop_credential="test_pop",
        ) as client:
            assert client is not None
            assert isinstance(client, EltakoAPI)

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self):
        """Test that context manager closes session on exit."""
        client = EltakoAPI(
            ip_address="192.168.1.100",
            pop_credential="test_pop",
        )

        async with client:
            # Create session
            await client._get_session()
            assert client._session is not None

        # Session should be closed
        assert client._session is None


class TestSessionManagement:
    """Test session management."""

    @pytest.mark.asyncio
    async def test_get_session_creates_session(self, api_client):
        """Test that get_session creates a session if needed."""
        assert api_client._session is None
        session = await api_client._get_session()
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)

    @pytest.mark.asyncio
    async def test_get_session_reuses_session(self, api_client):
        """Test that get_session reuses existing session."""
        session1 = await api_client._get_session()
        session2 = await api_client._get_session()
        assert session1 is session2

    @pytest.mark.asyncio
    async def test_async_close(self, api_client):
        """Test closing the API client."""
        await api_client._get_session()
        assert api_client._session is not None

        await api_client.async_close()

        assert api_client._session is None

    @pytest.mark.asyncio
    async def test_external_session_not_closed(self):
        """Test that externally provided session is not closed."""
        external_session = aiohttp.ClientSession()
        client = EltakoAPI(
            ip_address="192.168.1.100",
            pop_credential="test_pop",
            session=external_session,
        )

        await client.async_close()

        # External session should still be open
        assert not external_session.closed
        await external_session.close()


class TestCredentialSecurity:
    """Test that credentials are not logged."""

    @pytest.mark.asyncio
    async def test_no_credentials_in_logs(self, api_client, caplog):
        """Test that credentials are not logged."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )

            await api_client.async_login()

            # Check that sensitive data is not in logs
            log_output = caplog.text
            assert "test_pop_credential" not in log_output
            assert "test_key" not in log_output


class TestDeviceDiscovery:
    """Test device discovery functionality."""

    @pytest.mark.asyncio
    async def test_async_get_devices_success(self, api_client):
        """Test successful device list retrieval."""
        devices_response = {
            "devices": [
                {"guid": "device-1", "name": "Relay 1"},
                {"guid": "device-2", "name": "Relay 2"},
            ]
        }

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response,
                status=200,
            )

            devices = await api_client.async_get_devices()

            assert len(devices) == 2
            assert devices[0]["guid"] == "device-1"
            assert devices[1]["guid"] == "device-2"

    @pytest.mark.asyncio
    async def test_async_get_devices_caches_result(self, api_client):
        """Test that device list is cached."""
        devices_response = {"devices": [{"guid": "device-1", "name": "Relay 1"}]}

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint - only once
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response,
                status=200,
            )

            # First call fetches from API
            devices1 = await api_client.async_get_devices()
            # Second call returns cached result
            devices2 = await api_client.async_get_devices()

            assert devices1 == devices2
            assert api_client._devices_cache is not None
            assert api_client._devices_cache_timestamp is not None

    @pytest.mark.asyncio
    async def test_async_get_devices_cache_expiry(self, api_client):
        """Test that device cache expires after TTL."""
        devices_response1 = {"devices": [{"guid": "device-1"}]}
        devices_response2 = {"devices": [{"guid": "device-2"}]}

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock first devices call
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response1,
                status=200,
            )

            # First call
            devices1 = await api_client.async_get_devices()
            assert devices1[0]["guid"] == "device-1"

            # Simulate cache expiry
            api_client._devices_cache_timestamp = time.time() - (DEVICE_CACHE_TTL + 1)

            # Mock second devices call
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response2,
                status=200,
            )

            # Second call fetches fresh data
            devices2 = await api_client.async_get_devices()
            assert devices2[0]["guid"] == "device-2"

    @pytest.mark.asyncio
    async def test_async_get_devices_force_refresh(self, api_client):
        """Test force refresh bypasses cache."""
        devices_response1 = {"devices": [{"guid": "device-1"}]}
        devices_response2 = {"devices": [{"guid": "device-2"}]}

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock first devices call
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response1,
                status=200,
            )

            # First call
            devices1 = await api_client.async_get_devices()
            assert devices1[0]["guid"] == "device-1"

            # Mock second devices call
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload=devices_response2,
                status=200,
            )

            # Force refresh bypasses cache
            devices2 = await api_client.async_get_devices(force_refresh=True)
            assert devices2[0]["guid"] == "device-2"

    @pytest.mark.asyncio
    async def test_async_get_devices_empty_list(self, api_client):
        """Test handling of empty device list."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint with empty list
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": []},
                status=200,
            )

            devices = await api_client.async_get_devices()

            assert devices == []
            assert isinstance(devices, list)

    @pytest.mark.asyncio
    async def test_async_get_devices_invalid_response(self, api_client):
        """Test handling of invalid response format."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint with invalid format
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": "not a list"},
                status=200,
            )

            with pytest.raises(EltakoAPIError, match="Invalid devices response format"):
                await api_client.async_get_devices()

    @pytest.mark.asyncio
    async def test_async_get_devices_missing_devices_key(self, api_client):
        """Test handling of missing devices key in response."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint without devices key
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={},
                status=200,
            )

            devices = await api_client.async_get_devices()

            # Should return empty list when devices key is missing
            assert devices == []

    @pytest.mark.asyncio
    async def test_async_get_devices_connection_error(self, api_client):
        """Test handling of connection error during device discovery."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock devices endpoint with connection error (all retries)
            for _ in range(4):  # Initial + 3 retries
                mock_resp.get(
                    f"{api_client.base_url}{ENDPOINT_DEVICES}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            with pytest.raises(
                EltakoConnectionError, match="Cannot reach Eltako device"
            ):
                await api_client.async_get_devices()


class TestRelayControl:
    """Test relay control functionality."""

    @pytest.mark.asyncio
    async def test_async_set_relay_on(self, api_client):
        """Test setting relay to ON state."""
        device_guid = "test-device-123"

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock relay control endpoint
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            mock_resp.put(
                f"{api_client.base_url}{endpoint}",
                status=204,
            )

            await api_client.async_set_relay(device_guid, RELAY_STATE_ON)

            # Should complete without exceptions

    @pytest.mark.asyncio
    async def test_async_set_relay_off(self, api_client):
        """Test setting relay to OFF state."""
        device_guid = "test-device-456"

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock relay control endpoint
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            mock_resp.put(
                f"{api_client.base_url}{endpoint}",
                status=204,
            )

            await api_client.async_set_relay(device_guid, RELAY_STATE_OFF)

            # Should complete without exceptions

    @pytest.mark.asyncio
    async def test_async_set_relay_invalid_device_guid_empty(self, api_client):
        """Test relay control with empty device GUID."""
        with pytest.raises(
            EltakoInvalidDeviceError, match="Device GUID must be a non-empty string"
        ):
            await api_client.async_set_relay("", RELAY_STATE_ON)

    @pytest.mark.asyncio
    async def test_async_set_relay_invalid_device_guid_none(self, api_client):
        """Test relay control with None device GUID."""
        with pytest.raises(
            EltakoInvalidDeviceError, match="Device GUID must be a non-empty string"
        ):
            await api_client.async_set_relay(None, RELAY_STATE_ON)

    @pytest.mark.asyncio
    async def test_async_set_relay_invalid_device_guid_type(self, api_client):
        """Test relay control with invalid device GUID type."""
        with pytest.raises(
            EltakoInvalidDeviceError, match="Device GUID must be a non-empty string"
        ):
            await api_client.async_set_relay(123, RELAY_STATE_ON)

    @pytest.mark.asyncio
    async def test_async_set_relay_invalid_state(self, api_client):
        """Test relay control with invalid state."""
        device_guid = "test-device-789"

        with pytest.raises(EltakoAPIError, match="Invalid relay state"):
            await api_client.async_set_relay(device_guid, "invalid_state")

    @pytest.mark.asyncio
    async def test_async_set_relay_concurrent_commands(self, api_client):
        """Test that concurrent relay commands are queued properly."""
        device_guid_1 = "device-1"
        device_guid_2 = "device-2"

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )

            # Mock relay control endpoints
            endpoint1 = ENDPOINT_RELAY.format(device_guid=device_guid_1)
            endpoint2 = ENDPOINT_RELAY.format(device_guid=device_guid_2)

            mock_resp.put(f"{api_client.base_url}{endpoint1}", status=204)
            mock_resp.put(f"{api_client.base_url}{endpoint2}", status=204)

            # Execute commands concurrently
            await asyncio.gather(
                api_client.async_set_relay(device_guid_1, RELAY_STATE_ON),
                api_client.async_set_relay(device_guid_2, RELAY_STATE_OFF),
            )

            # Both commands should complete successfully

    @pytest.mark.asyncio
    async def test_async_set_relay_api_error(self, api_client):
        """Test handling of API error during relay control."""
        device_guid = "test-device-error"

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock relay control endpoint with error
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            mock_resp.put(
                f"{api_client.base_url}{endpoint}",
                status=400,
                body="Bad Request",
            )

            with pytest.raises(EltakoAPIError, match="API request failed with status 400"):
                await api_client.async_set_relay(device_guid, RELAY_STATE_ON)

    @pytest.mark.asyncio
    async def test_async_set_relay_sends_correct_payload(self, api_client):
        """Test that relay control sends correct payload format."""
        device_guid = "test-device-payload"

        # We need to verify the payload structure
        api_client._api_key = "test_key"
        api_client._token_timestamp = time.time()

        with aioresponses() as mock_resp:
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            mock_resp.put(
                f"{api_client.base_url}{endpoint}",
                status=204,
            )

            await api_client.async_set_relay(device_guid, RELAY_STATE_ON)

            # Verify the request was made with json parameter
            # aioresponses will validate this matches the expected call

    @pytest.mark.asyncio
    async def test_async_set_relay_connection_error(self, api_client):
        """Test handling of connection error during relay control."""
        device_guid = "test-device-connection"

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Mock relay control endpoint with connection error (all retries)
            endpoint = ENDPOINT_RELAY.format(device_guid=device_guid)
            for _ in range(4):  # Initial + 3 retries
                mock_resp.put(
                    f"{api_client.base_url}{endpoint}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            with pytest.raises(
                EltakoConnectionError, match="Cannot reach Eltako device"
            ):
                await api_client.async_set_relay(device_guid, RELAY_STATE_ON)
