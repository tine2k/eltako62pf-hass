"""Tests for Eltako ESR62PF-IP config flow."""
import ssl
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.eltako_esr62pf.config_flow import (
    EltakoConfigFlow,
)
from custom_components.eltako_esr62pf.const import (
    CONF_POP_CREDENTIAL,
    DEFAULT_PORT,
    DOMAIN,
)
from custom_components.eltako_esr62pf.exceptions import (
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)


@pytest.fixture
def mock_setup_entry():
    """Mock async_setup_entry."""
    with patch(
        "custom_components.eltako_esr62pf.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


# Note: _validate_ipv4 tests were removed as the function is now part of the
# voluptuous/cv validation and doesn't need separate testing


async def test_form_display(hass: HomeAssistant):
    """Test that the form is displayed on first step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_successful_config_flow(hass: HomeAssistant, mock_setup_entry):
    """Test successful configuration flow."""
    # Mock the API login
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        # Start the flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Submit user input
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify the flow completed successfully
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Eltako ESR62PF (192.168.1.100)"
        assert result["data"] == {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PORT: 443,
            CONF_POP_CREDENTIAL: "test_pop",
        }

        # Verify API was called correctly
        mock_api_class.assert_called_once_with(
            ip_address="192.168.1.100",
            pop_credential="test_pop",
            port=443,
            verify_ssl=False,
        )
        mock_api.async_login.assert_called_once()
        mock_api.async_close.assert_called_once()


async def test_port_default_value(hass: HomeAssistant, mock_setup_entry):
    """Test that port defaults to 443."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Submit without explicit port (should use default)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify default port was used
        assert result["data"][CONF_PORT] == DEFAULT_PORT


async def test_invalid_auth_error(hass: HomeAssistant):
    """Test handling of invalid PoP credential."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(side_effect=EltakoAuthenticationError("Invalid"))
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "wrong_pop",
            },
        )

        # Verify error is shown
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_connection_error(hass: HomeAssistant):
    """Test handling of connection errors."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(
            side_effect=EltakoConnectionError("Cannot connect")
        )
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify error is shown
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_timeout_error(hass: HomeAssistant):
    """Test handling of timeout errors."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(side_effect=EltakoTimeoutError("Timeout"))
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify error is shown
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "timeout_connect"}


async def test_ssl_error(hass: HomeAssistant):
    """Test handling of SSL certificate errors."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(side_effect=ssl.SSLError("SSL error"))
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify error is shown
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "ssl_error"}


async def test_unknown_error(hass: HomeAssistant):
    """Test handling of unexpected errors."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(side_effect=Exception("Unexpected"))
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify error is shown
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_duplicate_device_prevention(hass: HomeAssistant, mock_setup_entry):
    """Test that duplicate devices (same IP:Port) are prevented."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        # Create first entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Try to create duplicate entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify duplicate is rejected
        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "already_configured"


async def test_multiple_independent_devices(hass: HomeAssistant, mock_setup_entry):
    """Test that multiple devices can be configured independently."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        # Create first device
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result1 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop_1",
            },
        )
        assert result1["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Create second device with different IP
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.101",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop_2",
            },
        )
        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Create third device with different port
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result3 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 8443,
                CONF_POP_CREDENTIAL: "test_pop_3",
            },
        )
        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Verify all three devices are configured
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 3


async def test_api_close_called_on_error(hass: HomeAssistant):
    """Test that API client is properly closed even when errors occur."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(side_effect=EltakoConnectionError("Error"))
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        # Verify async_close was called even though login failed
        mock_api.async_close.assert_called_once()


async def test_unique_id_generation(hass: HomeAssistant, mock_setup_entry):
    """Test that unique ID is correctly generated from IP and port."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 8443,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

        # Get the created entry and verify unique_id
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 1
        assert entries[0].unique_id == "192.168.1.100:8443"


async def test_credentials_stored_securely(hass: HomeAssistant, mock_setup_entry):
    """Test that credentials are stored in the config entry."""
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI"
    ) as mock_api_class:
        mock_api = AsyncMock()
        mock_api.async_login = AsyncMock(return_value="test_api_key")
        mock_api.async_close = AsyncMock()
        mock_api_class.return_value = mock_api

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: 443,
                CONF_POP_CREDENTIAL: "secret_credential",
            },
        )

        # Verify credentials are stored in config entry data
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 1
        assert entries[0].data[CONF_POP_CREDENTIAL] == "secret_credential"
        assert entries[0].data[CONF_IP_ADDRESS] == "192.168.1.100"
        assert entries[0].data[CONF_PORT] == 443
