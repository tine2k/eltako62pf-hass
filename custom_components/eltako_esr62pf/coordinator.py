"""DataUpdateCoordinator for Eltako ESR62PF-IP integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EltakoAPI
from .const import (
    ERROR_MSG_API_ERROR,
    ERROR_MSG_AUTHENTICATION,
    ERROR_MSG_CONNECTION,
    ERROR_MSG_TIMEOUT,
    MAX_CONSECUTIVE_FAILURES,
    NOTIFICATION_ID_PREFIX,
)
from .exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


def _has_relay_function(device: dict[str, Any]) -> bool:
    """Check if a device has relay control capability.

    Args:
        device: Device data dictionary from API

    Returns:
        True if device has a function with identifier "relay", False otherwise
    """
    functions = device.get("functions", [])
    if not isinstance(functions, list):
        return False

    for function in functions:
        if isinstance(function, dict) and function.get("identifier") == "relay":
            return True

    return False


class EltakoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Eltako device data.

    Supports both optimistic updates (immediate UI feedback) and optional polling.
    By default, polling is disabled (update_interval=None) and the coordinator
    relies on optimistic updates when switch entities are controlled.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api: EltakoAPI,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api: EltakoAPI client instance
            update_interval: Optional polling interval (None = no polling)
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Eltako ESR62PF",
            update_interval=update_interval,
        )
        self.api = api
        self._devices: dict[str, Any] = {}
        self._consecutive_failures = 0
        self._last_error: str | None = None
        self._notification_shown = False

    def _get_notification_id(self) -> str:
        """Get the notification ID for this coordinator.

        Returns:
            Notification ID string
        """
        return f"{NOTIFICATION_ID_PREFIX}_{self.api._ip_address}"

    async def _show_persistent_notification(self, error_msg: str, error_type: str) -> None:
        """Show a persistent notification for errors.

        Args:
            error_msg: The error message to display
            error_type: Type of error (connection, authentication, etc.)
        """
        if self._notification_shown:
            return

        notification_id = self._get_notification_id()
        title = "Eltako ESR62PF-IP Connection Error"

        # Create user-friendly message with troubleshooting steps
        message = f"{error_msg}\n\n"

        if error_type == "connection":
            message += (
                "**Troubleshooting Steps:**\n"
                "- Verify the device is powered on\n"
                "- Check network connectivity\n"
                "- Ensure firewall allows HTTPS traffic\n"
                "- Verify IP address and port are correct"
            )
        elif error_type == "authentication":
            message += (
                "**Troubleshooting Steps:**\n"
                "- Verify the PoP credential in integration settings\n"
                "- Reconfigure the integration if needed"
            )
        elif error_type == "timeout":
            message += (
                "**Troubleshooting Steps:**\n"
                "- Check network latency to device\n"
                "- Verify device is not overloaded\n"
                "- Try restarting the device"
            )
        else:
            message += (
                "**Troubleshooting Steps:**\n"
                "- Check device logs for details\n"
                "- Try restarting the integration"
            )

        persistent_notification.create(
            self.hass,
            message,
            title,
            notification_id,
        )
        self._notification_shown = True
        _LOGGER.debug("Created persistent notification for %s error", error_type)

    async def _clear_persistent_notification(self) -> None:
        """Clear the persistent notification if it was shown."""
        if not self._notification_shown:
            return

        notification_id = self._get_notification_id()
        persistent_notification.dismiss(self.hass, notification_id)
        self._notification_shown = False
        _LOGGER.debug("Cleared persistent notification")

    async def _handle_update_success(self, device_data: dict[str, Any]) -> None:
        """Handle successful update - clear errors and restore devices.

        Args:
            device_data: Successfully fetched device data
        """
        # Check if we're recovering from failures
        was_failing = self._consecutive_failures > 0

        # Reset failure tracking
        self._consecutive_failures = 0
        self._last_error = None

        if was_failing:
            _LOGGER.info("Connection restored to Eltako device")

            # Clear persistent notification on recovery
            await self._clear_persistent_notification()

            # Mark all devices as available again
            for device_guid in device_data:
                device_data[device_guid]["available"] = True

    async def _handle_update_failure(
        self, error: Exception, error_type: str, error_msg: str
    ) -> None:
        """Handle update failure - track errors and show notifications.

        Args:
            error: The exception that occurred
            error_type: Type of error for notification
            error_msg: User-friendly error message
        """
        self._consecutive_failures += 1
        self._last_error = str(error)

        # Mark all devices as unavailable
        for device_guid in self._devices:
            self._devices[device_guid]["available"] = False

        # Show persistent notification after MAX_CONSECUTIVE_FAILURES
        if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            await self._show_persistent_notification(error_msg, error_type)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.

        This method is called automatically when polling is enabled.
        When polling is disabled (update_interval=None), this method
        is not called automatically.

        Returns:
            Dictionary mapping device GUIDs to their state data

        Raises:
            UpdateFailed: If unable to fetch data from API
        """
        try:
            _LOGGER.debug("Fetching device states from API")

            # Fetch device list from API
            devices = await self.api.async_get_devices()

            # Filter devices to only include those with relay control capability
            relay_devices = [d for d in devices if _has_relay_function(d)]

            _LOGGER.debug(
                "Filtered devices: %d relay-capable out of %d total devices",
                len(relay_devices),
                len(devices),
            )

            # Transform API response to coordinator data format
            # Note: The API returns device metadata but not current relay states
            # For now, we'll initialize devices and preserve existing states
            device_data: dict[str, Any] = {}

            for device in relay_devices:
                device_guid = device.get("guid")
                if not device_guid:
                    _LOGGER.warning("Device missing GUID, skipping: %s", device)
                    continue

                # Preserve existing state if available, otherwise default to unknown
                if device_guid in self._devices:
                    device_data[device_guid] = self._devices[device_guid]
                else:
                    device_data[device_guid] = {
                        "state": None,  # Unknown state until first control
                        "available": True,
                        "name": device.get("name", f"Relay {device_guid[:8]}"),
                        "guid": device_guid,
                    }

            # Handle successful update
            await self._handle_update_success(device_data)

            self._devices = device_data
            _LOGGER.debug("Successfully fetched %d devices", len(device_data))

            return device_data

        except EltakoAuthenticationError as err:
            error_msg = ERROR_MSG_AUTHENTICATION
            _LOGGER.error("Authentication failed during device fetch: %s", err)
            await self._handle_update_failure(err, "authentication", error_msg)
            raise UpdateFailed(error_msg) from err

        except EltakoConnectionError as err:
            error_msg = ERROR_MSG_CONNECTION.format(
                ip=self.api._ip_address, port=self.api._port
            )
            _LOGGER.warning("Connection error during device fetch: %s", err)
            await self._handle_update_failure(err, "connection", error_msg)
            raise UpdateFailed(error_msg) from err

        except EltakoTimeoutError as err:
            error_msg = ERROR_MSG_TIMEOUT
            _LOGGER.warning("Timeout during device fetch: %s", err)
            await self._handle_update_failure(err, "timeout", error_msg)
            raise UpdateFailed(error_msg) from err

        except EltakoAPIError as err:
            error_msg = ERROR_MSG_API_ERROR.format(error=str(err))
            _LOGGER.error("API error during device fetch: %s", err)
            await self._handle_update_failure(err, "api", error_msg)
            raise UpdateFailed(error_msg) from err

        except Exception as err:
            error_msg = f"Unexpected error: {err}"
            _LOGGER.exception("Unexpected error during device fetch: %s", err)
            await self._handle_update_failure(err, "unexpected", error_msg)
            raise UpdateFailed(error_msg) from err

    async def async_set_device_state(
        self, device_guid: str, state: str
    ) -> None:
        """Set device state optimistically (without polling).

        This method updates the coordinator data immediately to provide
        instant UI feedback, without waiting for the next poll interval.
        This is the primary method for state updates when polling is disabled.

        Args:
            device_guid: GUID of the device to update
            state: New relay state ('on' or 'off')
        """
        _LOGGER.debug("Setting optimistic state for %s to %s", device_guid, state)

        # Initialize device data if not present
        if device_guid not in self._devices:
            self._devices[device_guid] = {
                "state": state,
                "available": True,
                "name": f"Relay {device_guid[:8]}",
                "guid": device_guid,
            }
        else:
            # Update existing device state
            self._devices[device_guid]["state"] = state
            self._devices[device_guid]["available"] = True

        # Notify all listeners (entities) of the state change
        self.async_set_updated_data(self._devices)

        _LOGGER.debug("Optimistic state update complete for %s", device_guid)

    async def async_mark_device_unavailable(self, device_guid: str) -> None:
        """Mark a device as unavailable after a failed operation.

        Args:
            device_guid: GUID of the device to mark unavailable
        """
        if device_guid in self._devices:
            _LOGGER.warning("Marking device %s as unavailable", device_guid)
            self._devices[device_guid]["available"] = False
            self.async_set_updated_data(self._devices)

    @property
    def consecutive_failures(self) -> int:
        """Get the number of consecutive failures.

        Returns:
            Number of consecutive update failures
        """
        return self._consecutive_failures

    @property
    def last_error(self) -> str | None:
        """Get the last error message.

        Returns:
            Last error message or None
        """
        return self._last_error

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh of data.

        This is called during integration setup. We'll fetch the device list
        to populate the coordinator with available devices.
        """
        await super().async_config_entry_first_refresh()
