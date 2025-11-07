"""Config flow for Eltako ESR62PF-IP integration."""
from __future__ import annotations

import ipaddress
import logging
import ssl
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import EltakoAPI
from .const import (
    CONF_POP_CREDENTIAL,
    DEFAULT_PORT,
    DOMAIN,
)
from .exceptions import (
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


def _validate_ipv4(value: str) -> str:
    """Validate that the input is a valid IPv4 address.

    Args:
        value: IP address string to validate

    Returns:
        The validated IP address string

    Raises:
        vol.Invalid: If the IP address is not valid IPv4
    """
    try:
        ipaddress.IPv4Address(value)
        return value
    except ValueError as err:
        raise vol.Invalid("Invalid IPv4 address") from err


# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): _validate_ipv4,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_POP_CREDENTIAL): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.

    Args:
        hass: Home Assistant instance
        data: User input data

    Returns:
        Dictionary with "title" key containing the device title

    Raises:
        EltakoAuthenticationError: If authentication fails
        EltakoConnectionError: If connection fails
        EltakoTimeoutError: If connection times out
    """
    # Create API client to test connection
    api = EltakoAPI(
        ip_address=data[CONF_IP_ADDRESS],
        pop_credential=data[CONF_POP_CREDENTIAL],
        port=data[CONF_PORT],
        verify_ssl=False,  # Self-signed certificates are common
    )

    try:
        # Attempt to authenticate
        await api.async_login()

        # Return info that you want to store in the config entry
        return {"title": f"Eltako ESR62PF ({data[CONF_IP_ADDRESS]})"}
    finally:
        # Always close the API client
        await api.async_close()


class EltakoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eltako ESR62PF-IP."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        Args:
            user_input: User input data or None if first display

        Returns:
            FlowResult indicating next step or entry creation
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Create unique ID from IP and port
            unique_id = f"{user_input[CONF_IP_ADDRESS]}:{user_input[CONF_PORT]}"

            # Check if already configured
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                # Validate connection
                info = await validate_input(self.hass, user_input)
            except EltakoAuthenticationError:
                _LOGGER.error("Authentication failed: Invalid PoP credential")
                errors["base"] = "invalid_auth"
            except EltakoConnectionError as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except EltakoTimeoutError:
                _LOGGER.error("Connection timeout")
                errors["base"] = "timeout_connect"
            except ssl.SSLError as err:
                _LOGGER.error("SSL error: %s", err)
                errors["base"] = "ssl_error"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                # Connection successful, create entry
                return self.async_create_entry(title=info["title"], data=user_input)

        # Show form (initial display or after error)
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
