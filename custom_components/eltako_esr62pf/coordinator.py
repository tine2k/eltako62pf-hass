"""DataUpdateCoordinator for Eltako ESR62PF-IP integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EltakoAPI
from .exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


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

            # Transform API response to coordinator data format
            # Note: The API returns device metadata but not current relay states
            # For now, we'll initialize devices and preserve existing states
            device_data: dict[str, Any] = {}

            for device in devices:
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

            self._devices = device_data
            _LOGGER.debug("Successfully fetched %d devices", len(device_data))

            return device_data

        except EltakoAuthenticationError as err:
            _LOGGER.error("Authentication failed during device fetch: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except EltakoConnectionError as err:
            _LOGGER.warning("Connection error during device fetch: %s", err)
            # Mark all devices as unavailable
            for device_guid in self._devices:
                self._devices[device_guid]["available"] = False
            raise UpdateFailed(f"Connection error: {err}") from err

        except EltakoTimeoutError as err:
            _LOGGER.warning("Timeout during device fetch: %s", err)
            # Mark all devices as unavailable
            for device_guid in self._devices:
                self._devices[device_guid]["available"] = False
            raise UpdateFailed(f"Timeout error: {err}") from err

        except EltakoAPIError as err:
            _LOGGER.error("API error during device fetch: %s", err)
            raise UpdateFailed(f"API error: {err}") from err

        except Exception as err:
            _LOGGER.exception("Unexpected error during device fetch: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

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

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh of data.

        This is called during integration setup. We'll fetch the device list
        to populate the coordinator with available devices.
        """
        await super().async_config_entry_first_refresh()
