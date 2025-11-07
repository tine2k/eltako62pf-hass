"""The Eltako ESR62PF-IP integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, Platform

from .api import EltakoAPI
from .const import (
    CONF_POLL_INTERVAL,
    CONF_POP_CREDENTIAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .coordinator import EltakoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

__version__ = "1.0.0"

PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eltako ESR62PF-IP from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry containing device configuration

    Returns:
        True if setup was successful
    """
    # Extract configuration
    ip_address = entry.data[CONF_IP_ADDRESS]
    port = entry.data[CONF_PORT]
    pop_credential = entry.data[CONF_POP_CREDENTIAL]

    # Get polling interval from options (if configured via Options Flow)
    # Default is None (no polling) - optimistic updates only
    poll_interval_seconds = entry.options.get(CONF_POLL_INTERVAL)
    update_interval = (
        timedelta(seconds=poll_interval_seconds) if poll_interval_seconds else None
    )

    _LOGGER.debug(
        "Setting up Eltako integration for %s:%s (polling: %s)",
        ip_address,
        port,
        "enabled" if update_interval else "disabled",
    )

    # Create API client
    api = EltakoAPI(
        ip_address=ip_address,
        pop_credential=pop_credential,
        port=port,
        verify_ssl=False,  # Self-signed certificates are common
        timeout=DEFAULT_TIMEOUT,
    )

    # Create coordinator
    coordinator = EltakoDataUpdateCoordinator(
        hass=hass,
        api=api,
        update_interval=update_interval,
    )

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data for access by platform entities
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Eltako integration setup complete for %s:%s", ip_address, port)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        True if unload was successful
    """
    _LOGGER.debug("Unloading Eltako integration for entry %s", entry.entry_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Retrieve coordinator
        coordinator: EltakoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

        # Close API client
        await coordinator.api.async_close()

        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)

        _LOGGER.info("Eltako integration unloaded successfully")

    return unload_ok
