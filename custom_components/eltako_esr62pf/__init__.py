"""The Eltako ESR62PF-IP integration."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import DOMAIN

__version__ = "1.0.0"


async def async_setup_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Set up Eltako ESR62PF-IP from a config entry."""
    # This will be implemented in task-3 (config flow)
    # and task-4 (coordinator)
    return True


async def async_unload_entry(hass: "HomeAssistant", entry: "ConfigEntry") -> bool:
    """Unload a config entry."""
    # This will be implemented with the coordinator
    return True
