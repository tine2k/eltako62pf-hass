"""Switch platform for Eltako ESR62PF-IP integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN, RELAY_STATE_ON, RELAY_STATE_OFF
from .coordinator import EltakoDataUpdateCoordinator
from .exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eltako switch entities from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: EltakoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create switch entities for each device in coordinator data
    entities = []
    if coordinator.data:
        for device_guid, device_data in coordinator.data.items():
            _LOGGER.debug("Creating switch entity for device %s", device_guid)
            entities.append(EltakoSwitchEntity(coordinator, device_guid, device_data))

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d Eltako switch entities", len(entities))
    else:
        _LOGGER.warning("No devices found to create switch entities")


class EltakoSwitchEntity(
    CoordinatorEntity[EltakoDataUpdateCoordinator], SwitchEntity, RestoreEntity
):
    """Representation of an Eltako relay as a switch entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EltakoDataUpdateCoordinator,
        device_guid: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch entity.

        Args:
            coordinator: Data update coordinator
            device_guid: Unique GUID of the device
            device_data: Device data from coordinator
        """
        super().__init__(coordinator)
        self._device_guid = device_guid
        self._attr_unique_id = device_guid

        # Generate entity name from device data
        device_name = device_data.get("name", f"Relay {device_guid[:8]}")
        self._attr_name = device_name

        # Create suggested object_id for entity registry
        # This will result in entity_id like: switch.eltako_{sanitized_name}
        self._attr_suggested_object_id = f"eltako_{slugify(device_name)}"

        _LOGGER.debug(
            "Initialized switch entity: %s (GUID: %s)",
            self._attr_name,
            device_guid,
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant.

        Restore the last state from storage if available.
        """
        await super().async_added_to_hass()

        # Restore last state if available
        if (last_state := await self.async_get_last_state()) is not None:
            _LOGGER.debug(
                "Restoring previous state for %s: %s",
                self._device_guid,
                last_state.state,
            )

            # Restore the state in coordinator data
            if self._device_guid in self.coordinator._devices:
                # Convert "on"/"off" state to relay state constant
                if last_state.state == "on":
                    self.coordinator._devices[self._device_guid]["state"] = RELAY_STATE_ON
                elif last_state.state == "off":
                    self.coordinator._devices[self._device_guid]["state"] = RELAY_STATE_OFF

                _LOGGER.debug(
                    "Restored state for %s to %s",
                    self._device_guid,
                    last_state.state,
                )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for device registry.

        Returns:
            DeviceInfo object containing device metadata
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_guid)},
            name=self._attr_name,
            manufacturer="Eltako",
            model="ESR62PF-IP",
            sw_version="1.0.0",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on.

        Returns:
            True if on, False if off, None if unknown
        """
        if not self.coordinator.data:
            return None

        device_data = self.coordinator.data.get(self._device_guid)
        if not device_data:
            return None

        state = device_data.get("state")
        if state is None:
            return None

        return state == RELAY_STATE_ON

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        Returns:
            True if device is available, False otherwise
        """
        # First check if coordinator is available
        if not self.coordinator.last_update_success:
            return False

        # Then check device-specific availability
        if not self.coordinator.data:
            return False

        device_data = self.coordinator.data.get(self._device_guid)
        if not device_data:
            return False

        return device_data.get("available", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes.

        Returns:
            Dictionary of extra attributes
        """
        attributes = {
            "device_guid": self._device_guid,
            "connection_status": "connected" if self.available else "disconnected",
            "consecutive_failures": self.coordinator.consecutive_failures,
        }

        # Add last updated timestamp if available
        if hasattr(self.coordinator, "last_update_success_time") and self.coordinator.last_update_success_time:
            attributes["last_success"] = self.coordinator.last_update_success_time.isoformat()

        # Add last error if available
        if self.coordinator.last_error:
            attributes["last_error"] = self.coordinator.last_error

        # Add retry information for failed states
        if self.coordinator.consecutive_failures > 0:
            attributes["retry_count"] = self.coordinator.consecutive_failures

        return attributes

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on.

        Args:
            **kwargs: Additional arguments (unused)
        """
        _LOGGER.debug("Turning on switch %s", self._device_guid)

        try:
            # Send command to device
            await self.coordinator.api.async_set_relay(
                self._device_guid, RELAY_STATE_ON
            )

            # Update state optimistically for instant UI feedback
            await self.coordinator.async_set_device_state(
                self._device_guid, RELAY_STATE_ON
            )

            _LOGGER.debug("Successfully turned on switch %s", self._device_guid)

        except (
            EltakoAuthenticationError,
            EltakoConnectionError,
            EltakoTimeoutError,
            EltakoAPIError,
        ) as err:
            _LOGGER.error(
                "Failed to turn on switch %s: %s",
                self._device_guid,
                err,
            )
            # Mark device as unavailable
            await self.coordinator.async_mark_device_unavailable(self._device_guid)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off.

        Args:
            **kwargs: Additional arguments (unused)
        """
        _LOGGER.debug("Turning off switch %s", self._device_guid)

        try:
            # Send command to device
            await self.coordinator.api.async_set_relay(
                self._device_guid, RELAY_STATE_OFF
            )

            # Update state optimistically for instant UI feedback
            await self.coordinator.async_set_device_state(
                self._device_guid, RELAY_STATE_OFF
            )

            _LOGGER.debug("Successfully turned off switch %s", self._device_guid)

        except (
            EltakoAuthenticationError,
            EltakoConnectionError,
            EltakoTimeoutError,
            EltakoAPIError,
        ) as err:
            _LOGGER.error(
                "Failed to turn off switch %s: %s",
                self._device_guid,
                err,
            )
            # Mark device as unavailable
            await self.coordinator.async_mark_device_unavailable(self._device_guid)
            raise
