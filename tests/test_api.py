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
    ENDPOINT_LOGIN,
)
from custom_components.eltako_esr62pf.exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
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
        assert api_client_with_ssl._ssl_context is None  # Uses default

    def test_ssl_context_without_verification(self, api_client):
        """Test SSL context when verification is disabled."""
        assert api_client._ssl_context is not None
        assert isinstance(api_client._ssl_context, ssl.SSLContext)
        assert api_client._ssl_context.verify_mode == ssl.CERT_NONE
        assert api_client._ssl_context.check_hostname is False

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

            with pytest.raises(EltakoAuthenticationError, match="Invalid PoP credential"):
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

            with pytest.raises(EltakoConnectionError, match="Failed to connect to device"):
                await api_client.async_login()

    @pytest.mark.asyncio
    async def test_async_login_timeout(self, api_client):
        """Test login with timeout."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                exception=asyncio.TimeoutError(),
            )

            with pytest.raises(EltakoTimeoutError, match="Login request timed out"):
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

            with pytest.raises(EltakoConnectionError, match="Failed to connect after 3 retries"):
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
