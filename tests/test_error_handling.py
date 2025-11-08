"""Tests for comprehensive error handling and recovery."""
import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.eltako_esr62pf.api import EltakoAPI
from custom_components.eltako_esr62pf.const import (
    ENDPOINT_DEVICES,
    ENDPOINT_LOGIN,
    ERROR_MSG_AUTHENTICATION,
    ERROR_MSG_CONNECTION,
    ERROR_MSG_TIMEOUT,
    MAX_CONSECUTIVE_FAILURES,
    NOTIFICATION_ID_PREFIX,
)
from custom_components.eltako_esr62pf.coordinator import EltakoDataUpdateCoordinator
from custom_components.eltako_esr62pf.exceptions import (
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
        port=443,
        verify_ssl=False,
    )


@pytest.fixture
async def coordinator(hass: HomeAssistant, api_client):
    """Create a coordinator for testing."""
    return EltakoDataUpdateCoordinator(
        hass=hass,
        api=api_client,
        update_interval=timedelta(seconds=10),
    )


class TestExponentialBackoff:
    """Test exponential backoff retry logic."""

    @pytest.mark.asyncio
    async def test_connection_error_retries_with_backoff(self, api_client):
        """Test that connection errors trigger exponential backoff."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # First 2 attempts fail, 3rd succeeds
            for _ in range(2):
                mock_resp.get(
                    f"{api_client.base_url}/api/v0/devices",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )
            mock_resp.get(
                f"{api_client.base_url}/api/v0/devices",
                payload={"devices": []},
                status=200,
            )

            import time
            start = time.time()
            result = await api_client._make_request("GET", "/api/v0/devices")
            elapsed = time.time() - start

            # Should wait 2^0 + 2^1 = 3 seconds
            assert elapsed >= 3.0
            assert result == {"devices": []}

    @pytest.mark.asyncio
    async def test_timeout_retries_with_backoff(self, api_client):
        """Test that timeouts trigger exponential backoff."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # First attempt times out, 2nd succeeds
            mock_resp.get(
                f"{api_client.base_url}/api/v0/devices",
                exception=asyncio.TimeoutError(),
            )
            mock_resp.get(
                f"{api_client.base_url}/api/v0/devices",
                payload={"devices": []},
                status=200,
            )

            import time
            start = time.time()
            result = await api_client._make_request("GET", "/api/v0/devices")
            elapsed = time.time() - start

            # Should wait 2^0 = 1 second
            assert elapsed >= 1.0
            assert result == {"devices": []}

    @pytest.mark.asyncio
    async def test_max_retries_respected(self, api_client):
        """Test that max retries limit is respected."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # All 4 attempts fail (initial + 3 retries)
            for _ in range(4):
                mock_resp.get(
                    f"{api_client.base_url}/api/v0/devices",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            with pytest.raises(EltakoConnectionError):
                await api_client._make_request("GET", "/api/v0/devices")


class TestCoordinatorErrorHandling:
    """Test coordinator error handling and recovery."""

    @pytest.mark.asyncio
    async def test_consecutive_failures_tracking(self, hass, coordinator):
        """Test that consecutive failures are tracked correctly."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{coordinator.api.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # All device requests fail
            for _ in range(5):
                mock_resp.get(
                    f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                    repeat=True,
                )

            # Trigger 3 updates that fail
            for i in range(3):
                with pytest.raises(UpdateFailed):
                    await coordinator._async_update_data()
                assert coordinator.consecutive_failures == i + 1

    @pytest.mark.asyncio
    async def test_persistent_notification_after_max_failures(self, hass, coordinator):
        """Test that persistent notification is created after max failures."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{coordinator.api.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # All device requests fail
            for _ in range(10):
                mock_resp.get(
                    f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                    repeat=True,
                )

            # Fail MAX_CONSECUTIVE_FAILURES times
            for _ in range(MAX_CONSECUTIVE_FAILURES):
                with pytest.raises(UpdateFailed):
                    await coordinator._async_update_data()

            # Notification should be shown
            assert coordinator._notification_shown is True

    @pytest.mark.asyncio
    async def test_notification_cleared_on_recovery(self, hass, coordinator):
        """Test that notification is cleared when connection recovers."""
        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{coordinator.api.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )

            # Fail MAX_CONSECUTIVE_FAILURES times
            for _ in range(MAX_CONSECUTIVE_FAILURES):
                mock_resp.get(
                    f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            for _ in range(MAX_CONSECUTIVE_FAILURES):
                with pytest.raises(UpdateFailed):
                    await coordinator._async_update_data()

            assert coordinator._notification_shown is True

            # Now succeed
            mock_resp.get(
                f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": []},
                status=200,
            )

            await coordinator._async_update_data()

            # Notification should be cleared
            assert coordinator._notification_shown is False
            assert coordinator.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_devices_marked_unavailable_on_failure(self, hass, coordinator):
        """Test that devices are marked unavailable on connection failure."""
        # Setup initial devices
        coordinator._devices = {
            "device-1": {"state": "on", "available": True, "name": "Device 1", "guid": "device-1"},
            "device-2": {"state": "off", "available": True, "name": "Device 2", "guid": "device-2"},
        }

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{coordinator.api.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Fail
            mock_resp.get(
                f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                exception=aiohttp.ClientConnectorError(
                    connection_key=MagicMock(),
                    os_error=OSError("Connection refused"),
                ),
                repeat=True,
            )

            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

            # All devices should be marked unavailable
            assert coordinator._devices["device-1"]["available"] is False
            assert coordinator._devices["device-2"]["available"] is False

    @pytest.mark.asyncio
    async def test_devices_marked_available_on_recovery(self, hass, coordinator):
        """Test that devices are marked available on recovery."""
        # Setup initial unavailable devices
        coordinator._devices = {
            "device-1": {"state": "on", "available": False, "name": "Device 1", "guid": "device-1"},
        }
        coordinator._consecutive_failures = 2

        with aioresponses() as mock_resp:
            # Mock login
            mock_resp.post(
                f"{coordinator.api.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "test_key"},
                status=200,
            )
            # Succeed
            mock_resp.get(
                f"{coordinator.api.base_url}{ENDPOINT_DEVICES}",
                payload={
                    "devices": [
                        {"guid": "device-1", "name": "Device 1"},
                    ]
                },
                status=200,
            )

            await coordinator._async_update_data()

            # Device should be marked available
            assert coordinator._devices["device-1"]["available"] is True
            assert coordinator.consecutive_failures == 0


class TestTokenReauthentication:
    """Test automatic token re-authentication."""

    @pytest.mark.asyncio
    async def test_token_expiry_triggers_reauthentication(self, api_client):
        """Test that expired token triggers automatic re-authentication."""
        # Set expired token
        api_client._api_key = "expired_token"
        api_client._token_timestamp = 0.0  # Long expired

        with aioresponses() as mock_resp:
            # Mock re-authentication
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "new_token"},
                status=200,
            )
            # Mock actual request
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": []},
                status=200,
            )

            result = await api_client._make_request("GET", ENDPOINT_DEVICES)

            # Should have refreshed token
            assert api_client._api_key == "new_token"
            assert result == {"devices": []}

    @pytest.mark.asyncio
    async def test_401_response_triggers_reauthentication(self, api_client):
        """Test that 401 response triggers re-authentication."""
        api_client._api_key = "valid_but_rejected_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # First request returns 401
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                status=401,
            )
            # Mock re-authentication
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                payload={"apiKey": "new_token_after_401"},
                status=200,
            )
            # Retry request succeeds
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": []},
                status=200,
            )

            result = await api_client._make_request("GET", ENDPOINT_DEVICES)

            # Should have refreshed token and succeeded
            assert api_client._api_key == "new_token_after_401"
            assert result == {"devices": []}


class TestErrorMessages:
    """Test that error messages are clear and actionable."""

    @pytest.mark.asyncio
    async def test_connection_error_message(self, api_client):
        """Test connection error message contains helpful information."""
        with aioresponses() as mock_resp:
            for _ in range(4):
                mock_resp.post(
                    f"{api_client.base_url}{ENDPOINT_LOGIN}",
                    exception=aiohttp.ClientConnectorError(
                        connection_key=MagicMock(),
                        os_error=OSError("Connection refused"),
                    ),
                )

            with pytest.raises(EltakoConnectionError) as exc_info:
                await api_client.async_login()

            error_msg = str(exc_info.value)
            assert "192.168.1.100" in error_msg
            assert "443" in error_msg

    @pytest.mark.asyncio
    async def test_authentication_error_message(self, api_client):
        """Test authentication error message is clear."""
        with aioresponses() as mock_resp:
            mock_resp.post(
                f"{api_client.base_url}{ENDPOINT_LOGIN}",
                status=401,
            )

            with pytest.raises(EltakoAuthenticationError) as exc_info:
                await api_client.async_login()

            error_msg = str(exc_info.value)
            assert "Authentication failed" in error_msg or "PoP credential" in error_msg

    @pytest.mark.asyncio
    async def test_timeout_error_message(self, api_client):
        """Test timeout error message is clear."""
        with aioresponses() as mock_resp:
            for _ in range(4):
                mock_resp.post(
                    f"{api_client.base_url}{ENDPOINT_LOGIN}",
                    exception=asyncio.TimeoutError(),
                )

            with pytest.raises(EltakoTimeoutError) as exc_info:
                await api_client.async_login()

            error_msg = str(exc_info.value)
            assert "not responding" in error_msg or "timeout" in error_msg.lower()


class TestTemporaryNetworkIssues:
    """Test recovery from temporary network issues."""

    @pytest.mark.asyncio
    async def test_temporary_connection_issue_recovers(self, api_client):
        """Test that temporary connection issues don't cause permanent failure."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # First attempt fails
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                exception=aiohttp.ClientConnectorError(
                    connection_key=MagicMock(),
                    os_error=OSError("Temporary network issue"),
                ),
            )
            # Second attempt succeeds
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": [{"guid": "device-1"}]},
                status=200,
            )

            result = await api_client._make_request("GET", ENDPOINT_DEVICES)

            # Should recover and return data
            assert result == {"devices": [{"guid": "device-1"}]}

    @pytest.mark.asyncio
    async def test_temporary_timeout_recovers(self, api_client):
        """Test recovery from temporary timeout."""
        api_client._api_key = "valid_token"
        api_client._token_timestamp = 9999999999.0

        with aioresponses() as mock_resp:
            # First attempt times out
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                exception=asyncio.TimeoutError(),
            )
            # Second attempt succeeds
            mock_resp.get(
                f"{api_client.base_url}{ENDPOINT_DEVICES}",
                payload={"devices": [{"guid": "device-1"}]},
                status=200,
            )

            result = await api_client._make_request("GET", ENDPOINT_DEVICES)

            # Should recover and return data
            assert result == {"devices": [{"guid": "device-1"}]}


class TestConnectionStatusVisibility:
    """Test that connection status is visible in entity attributes."""

    @pytest.mark.asyncio
    async def test_consecutive_failures_property(self, hass, coordinator):
        """Test consecutive_failures property is accessible."""
        assert coordinator.consecutive_failures == 0

        coordinator._consecutive_failures = 2
        assert coordinator.consecutive_failures == 2

    @pytest.mark.asyncio
    async def test_last_error_property(self, hass, coordinator):
        """Test last_error property is accessible."""
        assert coordinator.last_error is None

        coordinator._last_error = "Test error message"
        assert coordinator.last_error == "Test error message"
