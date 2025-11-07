"""Config flow for Eltako ESR62PF-IP integration."""
from __future__ import annotations

import logging
import ssl
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .api import EltakoAPI
from .const import (
    CONF_POLL_INTERVAL,
    CONF_POP_CREDENTIAL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PORT,
    DOMAIN,
    MIN_POLL_INTERVAL,
)
from .exceptions import (
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


# Schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return EltakoOptionsFlowHandler(config_entry)

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


class EltakoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Eltako ESR62PF-IP integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Args:
            user_input: User input data or None if first display

        Returns:
            FlowResult indicating next step or options update
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate PoP credential if changed
            new_pop = user_input.get(CONF_POP_CREDENTIAL)
            old_pop = self.config_entry.data.get(CONF_POP_CREDENTIAL)

            if new_pop and new_pop != old_pop:
                # Test authentication with new credential
                api = EltakoAPI(
                    ip_address=self.config_entry.data[CONF_IP_ADDRESS],
                    pop_credential=new_pop,
                    port=self.config_entry.data[CONF_PORT],
                    verify_ssl=False,
                )

                try:
                    await api.async_login()
                except EltakoAuthenticationError:
                    _LOGGER.error("Authentication failed with new PoP credential")
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
                finally:
                    await api.async_close()

            # Validate polling interval
            enable_polling = user_input.get("enable_polling", False)
            poll_interval = user_input.get(CONF_POLL_INTERVAL)

            if enable_polling and poll_interval is not None:
                if poll_interval < MIN_POLL_INTERVAL:
                    errors["poll_interval"] = "invalid_poll_interval"

            # If no errors, save options
            if not errors:
                # Prepare options data
                options = {}

                # Save polling configuration
                if enable_polling and poll_interval is not None:
                    options[CONF_POLL_INTERVAL] = poll_interval
                # If polling disabled, don't include poll_interval (None will disable it)

                # Update config entry data if PoP credential changed
                if new_pop and new_pop != old_pop:
                    new_data = dict(self.config_entry.data)
                    new_data[CONF_POP_CREDENTIAL] = new_pop
                    self.hass.config_entries.async_update_entry(
                        self.config_entry, data=new_data
                    )

                return self.async_create_entry(title="", data=options)

        # Get current values for defaults
        current_pop = self.config_entry.data.get(CONF_POP_CREDENTIAL, "")
        current_poll_interval = self.config_entry.options.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )
        enable_polling = self.config_entry.options.get(CONF_POLL_INTERVAL) is not None

        # Build options schema
        options_schema = vol.Schema(
            {
                vol.Required(CONF_POP_CREDENTIAL, default=current_pop): str,
                vol.Required("enable_polling", default=enable_polling): bool,
                vol.Optional(
                    CONF_POLL_INTERVAL, default=current_poll_interval
                ): vol.All(cv.positive_int, vol.Range(min=MIN_POLL_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
