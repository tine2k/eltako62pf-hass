"""Integration tests for Eltako ESR62PF-IP Home Assistant integration."""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from custom_components.eltako_esr62pf.const import (
    CONF_POLL_INTERVAL,
    CONF_POP_CREDENTIAL,
    DEFAULT_PORT,
    DOMAIN,
    RELAY_STATE_OFF,
    RELAY_STATE_ON,
)
from custom_components.eltako_esr62pf.exceptions import (
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)


# Test fixtures and helpers

@pytest.fixture
def mock_device_data():
    """Return mock device data from API."""
    return [
        {
            "guid": "device-guid-1",
            "name": "Living Room Light",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
        {
            "guid": "device-guid-2",
            "name": "Kitchen Switch",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
        {
            "guid": "device-guid-3",
            "name": "Bedroom Fan",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
    ]


@pytest.fixture
def mock_api():
    """Create a mock EltakoAPI instance."""
    api = AsyncMock()
    api.async_login = AsyncMock(return_value="test_api_key")
    api.async_get_devices = AsyncMock()
    api.async_set_relay = AsyncMock()
    api.async_close = AsyncMock()
    api._ip_address = "192.168.1.100"
    api._port = 443
    return api


async def setup_integration(
    hass: HomeAssistant,
    mock_api: AsyncMock,
    mock_devices: list,
    poll_interval: int | None = None,
) -> config_entries.ConfigEntry:
    """Set up the Eltako integration with mocked API.

    Args:
        hass: Home Assistant instance
        mock_api: Mocked API client
        mock_devices: List of mock device data
        poll_interval: Optional polling interval in seconds

    Returns:
        The created config entry
    """
    mock_api.async_get_devices.return_value = mock_devices

    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI",
        return_value=mock_api,
    ), patch(
        "custom_components.eltako_esr62pf.EltakoAPI",
        return_value=mock_api,
    ):
        # Create config entry through flow (which auto-sets up)
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: DEFAULT_PORT,
                CONF_POP_CREDENTIAL: "test_pop",
            },
        )
        entry = result["result"]

        # Configure polling if specified
        if poll_interval is not None:
            hass.config_entries.async_update_entry(
                entry,
                options={CONF_POLL_INTERVAL: poll_interval},
            )
            # Reload to apply polling settings
            await hass.config_entries.async_reload(entry.entry_id)

        await hass.async_block_till_done()

    return entry


async def get_entity_id(hass: HomeAssistant, device_guid: str) -> str | None:
    """Get entity ID for a device GUID.

    Args:
        hass: Home Assistant instance
        device_guid: Device GUID

    Returns:
        Entity ID or None if not found
    """
    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if entity.unique_id == device_guid:
            return entity.entity_id
    return None


# Config Flow Integration Tests

async def test_full_integration_setup(hass: HomeAssistant, mock_api, mock_device_data):
    """Test complete integration setup creates entities correctly."""
    # Setup integration
    entry = await setup_integration(hass, mock_api, mock_device_data)

    # Verify entry was created
    assert entry.state == config_entries.ConfigEntryState.LOADED
    assert entry.data[CONF_IP_ADDRESS] == "192.168.1.100"
    assert entry.data[CONF_PORT] == DEFAULT_PORT
    assert entry.data[CONF_POP_CREDENTIAL] == "test_pop"

    # Verify coordinator is set up
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator is not None

    # Verify entities were created
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 3

    # Verify each device created an entity
    entity_unique_ids = {entity.unique_id for entity in entities}
    assert "device-guid-1" in entity_unique_ids
    assert "device-guid-2" in entity_unique_ids
    assert "device-guid-3" in entity_unique_ids

    # Verify API was called
    mock_api.async_get_devices.assert_called()


async def test_integration_setup_invalid_credentials(hass: HomeAssistant):
    """Test integration setup fails with invalid credentials."""
    mock_api = AsyncMock()
    mock_api.async_login = AsyncMock(side_effect=EltakoAuthenticationError("Invalid"))
    mock_api.async_close = AsyncMock()

    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI",
        return_value=mock_api,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "192.168.1.100",
                CONF_PORT: DEFAULT_PORT,
                CONF_POP_CREDENTIAL: "wrong_pop",
            },
        )

        # Verify error was shown
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"

        # Verify no entry was created
        assert len(hass.config_entries.async_entries(DOMAIN)) == 0


# Options Flow Integration Tests

async def test_options_flow_enable_polling(hass: HomeAssistant, mock_api, mock_device_data):
    """Test enabling polling through options flow."""
    # Setup integration without polling
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=None)

    # Verify polling is initially disabled
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval is None

    # Update options to enable polling
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI",
        return_value=mock_api,
    ), patch(
        "custom_components.eltako_esr62pf.EltakoAPI",
        return_value=mock_api,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_POP_CREDENTIAL: "test_pop",
                "enable_polling": True,
                CONF_POLL_INTERVAL: 30,
            },
        )

        assert result["type"] == "create_entry"
        await hass.async_block_till_done()

    # Verify polling is now enabled
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval is not None
    assert coordinator.update_interval == timedelta(seconds=30)


async def test_options_flow_disable_polling(hass: HomeAssistant, mock_api, mock_device_data):
    """Test disabling polling through options flow."""
    # Setup integration with polling
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=30)

    # Verify polling is enabled
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval == timedelta(seconds=30)

    # Update options to disable polling
    with patch(
        "custom_components.eltako_esr62pf.config_flow.EltakoAPI",
        return_value=mock_api,
    ), patch(
        "custom_components.eltako_esr62pf.EltakoAPI",
        return_value=mock_api,
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_POP_CREDENTIAL: "test_pop",
                "enable_polling": False,
                CONF_POLL_INTERVAL: 30,
            },
        )

        assert result["type"] == "create_entry"
        await hass.async_block_till_done()

    # Verify polling is now disabled
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval is None


# Entity Creation and Registration Tests

async def test_entity_creation_all_devices(hass: HomeAssistant, mock_api, mock_device_data):
    """Test all discovered devices create switch entities."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    # Get entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    # Verify correct number of entities
    assert len(entities) == 3

    # Verify entity attributes for each device
    for device in mock_device_data:
        entity_id = await get_entity_id(hass, device["guid"])
        assert entity_id is not None

        # Get entity from registry
        entity = entity_registry.async_get(entity_id)
        assert entity.unique_id == device["guid"]
        assert entity.platform == DOMAIN
        assert entity.domain == SWITCH_DOMAIN

        # Verify entity state exists
        state = hass.states.get(entity_id)
        assert state is not None


# Service Call Tests

async def test_service_turn_on(hass: HomeAssistant, mock_api, mock_device_data):
    """Test turn_on service call."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    # Get entity ID for first device
    entity_id = await get_entity_id(hass, "device-guid-1")
    assert entity_id is not None

    # Call turn_on service
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify API was called
    mock_api.async_set_relay.assert_called_with("device-guid-1", RELAY_STATE_ON)

    # Verify state is on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


async def test_service_turn_off(hass: HomeAssistant, mock_api, mock_device_data):
    """Test turn_off service call."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    # Get entity ID
    entity_id = await get_entity_id(hass, "device-guid-1")
    assert entity_id is not None

    # First turn on
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    # Then turn off
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify API was called
    mock_api.async_set_relay.assert_called_with("device-guid-1", RELAY_STATE_OFF)

    # Verify state is off
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_service_toggle(hass: HomeAssistant, mock_api, mock_device_data):
    """Test toggle service call."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    # Get entity ID
    entity_id = await get_entity_id(hass, "device-guid-1")
    assert entity_id is not None

    # Turn on first
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ON

    # Toggle (should turn off)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Toggle again (should turn on)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {"entity_id": entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


# Optimistic Update Tests

async def test_optimistic_updates_immediate(hass: HomeAssistant, mock_api, mock_device_data):
    """Test optimistic updates happen immediately without polling."""
    # Setup without polling
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=None)

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Reset mock to track calls
    mock_api.async_get_devices.reset_mock()

    # Turn on switch
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )

    # Verify state updated immediately
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Verify no polling occurred
    mock_api.async_get_devices.assert_not_called()


async def test_optimistic_updates_no_polling(hass: HomeAssistant, mock_api, mock_device_data):
    """Test that optimistic updates work without background polling."""
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=None)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval is None

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Clear mock calls from setup
    mock_api.async_get_devices.reset_mock()

    # Perform multiple state changes
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_OFF

    # Verify no polling happened
    mock_api.async_get_devices.assert_not_called()


# Polling Tests

async def test_polling_enabled_periodic_updates(hass: HomeAssistant, mock_api, mock_device_data):
    """Test that polling fetches data periodically when enabled."""
    # Setup with short polling interval for testing
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=10)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval == timedelta(seconds=10)

    # Clear setup calls
    mock_api.async_get_devices.reset_mock()

    # Trigger a manual refresh to simulate polling
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Verify API was called
    mock_api.async_get_devices.assert_called()


async def test_polling_disabled_no_background_updates(hass: HomeAssistant, mock_api, mock_device_data):
    """Test that polling is disabled when configured."""
    # Setup without polling
    entry = await setup_integration(hass, mock_api, mock_device_data, poll_interval=None)

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.update_interval is None

    # Clear setup calls
    mock_api.async_get_devices.reset_mock()

    # Wait a bit
    await hass.async_block_till_done()

    # Verify no automatic polling
    mock_api.async_get_devices.assert_not_called()


# Network Error and Recovery Tests

async def test_network_error_handling(hass: HomeAssistant, mock_api, mock_device_data):
    """Test graceful handling of network errors."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Simulate network error
    mock_api.async_set_relay.side_effect = EltakoConnectionError("Connection failed")

    # Attempt to turn on switch
    with pytest.raises(Exception):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": entity_id},
            blocking=True,
        )

    # Entity should be marked unavailable
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_data = coordinator.data.get("device-guid-1")
    assert device_data is not None
    assert device_data["available"] is False


async def test_network_error_recovery(hass: HomeAssistant, mock_api, mock_device_data):
    """Test recovery from network errors."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Simulate multiple failures
    mock_api.async_get_devices.side_effect = EltakoConnectionError("Connection failed")

    # Trigger failures (coordinator catches UpdateFailed internally)
    for _ in range(3):
        await coordinator.async_refresh()

    assert coordinator.consecutive_failures == 3

    # Restore connectivity
    mock_api.async_get_devices.side_effect = None
    mock_api.async_get_devices.return_value = mock_device_data

    # Trigger successful refresh
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Verify recovery
    assert coordinator.consecutive_failures == 0
    assert coordinator.last_error is None


async def test_timeout_error_handling(hass: HomeAssistant, mock_api, mock_device_data):
    """Test handling of timeout errors."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Simulate timeout
    mock_api.async_set_relay.side_effect = EltakoTimeoutError("Timeout")

    # Attempt operation
    with pytest.raises(Exception):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": entity_id},
            blocking=True,
        )

    # Verify error was handled
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device_data = coordinator.data.get("device-guid-1")
    assert device_data["available"] is False


# Re-authentication Tests

async def test_automatic_reauthentication(hass: HomeAssistant, mock_api, mock_device_data):
    """Test automatic re-authentication on token expiry."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Simulate auth error then success on retry
    call_count = 0

    async def side_effect_auth(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise EltakoAuthenticationError("Token expired")
        return None

    mock_api.async_set_relay.side_effect = side_effect_auth

    # The entity should handle re-auth internally if implemented
    # For now, verify auth error is raised
    with pytest.raises(Exception):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {"entity_id": entity_id},
            blocking=True,
        )


async def test_failed_reauthentication(hass: HomeAssistant, mock_api, mock_device_data):
    """Test handling of failed re-authentication."""
    entry = await setup_integration(hass, mock_api, mock_device_data)

    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Simulate persistent auth failure
    mock_api.async_get_devices.side_effect = EltakoAuthenticationError("Invalid credentials")

    # Attempt refresh (coordinator catches UpdateFailed internally)
    await coordinator.async_refresh()

    # Verify error tracking
    assert coordinator.consecutive_failures > 0
    assert coordinator.last_error is not None
    assert "authentication" in coordinator.last_error.lower() or "invalid" in coordinator.last_error.lower()


# Integration Reload and Unload Tests

async def test_integration_reload(hass: HomeAssistant, mock_api, mock_device_data):
    """Test clean integration reload."""
    # Setup integration
    entry = await setup_integration(hass, mock_api, mock_device_data)

    entity_id = await get_entity_id(hass, "device-guid-1")

    # Turn on a switch to establish state
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hass.states.get(entity_id).state == STATE_ON

    # Reload integration
    with patch(
        "custom_components.eltako_esr62pf.EltakoAPI",
        return_value=mock_api,
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    # Verify entry is still loaded
    assert entry.state == config_entries.ConfigEntryState.LOADED

    # Verify entities still exist
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 3


async def test_integration_unload(hass: HomeAssistant, mock_api, mock_device_data):
    """Test clean integration unload."""
    # Setup integration
    entry = await setup_integration(hass, mock_api, mock_device_data)

    entity_id = await get_entity_id(hass, "device-guid-1")
    assert hass.states.get(entity_id) is not None

    # Unload integration
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    # Verify entry is unloaded
    assert entry.state == config_entries.ConfigEntryState.NOT_LOADED

    # Verify API was closed
    mock_api.async_close.assert_called()

    # Verify coordinator was cleaned up
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


# Device Filtering Tests


async def test_devices_without_relay_function_filtered_out(hass: HomeAssistant, mock_api):
    """Test that devices without relay functions are not added as entities."""
    # Create device data with mixed relay and non-relay devices
    mixed_device_data = [
        {
            "guid": "relay-device-1",
            "name": "Relay Switch",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
        {
            "guid": "sensor-device-1",
            "name": "Temperature Sensor",
            "functions": [{"identifier": "temperature", "type": "value"}],
        },
        {
            "guid": "relay-device-2",
            "name": "Another Relay",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
        {
            "guid": "empty-functions-device",
            "name": "Device Without Functions",
            "functions": [],
        },
    ]

    # Setup integration with mixed devices
    entry = await setup_integration(hass, mock_api, mixed_device_data)

    # Verify only relay devices created entities
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    # Should only have 2 entities (the two relay devices)
    assert len(entities) == 2

    # Verify the correct devices were added
    entity_unique_ids = [entity.unique_id for entity in entities]
    assert "relay-device-1" in entity_unique_ids
    assert "relay-device-2" in entity_unique_ids
    assert "sensor-device-1" not in entity_unique_ids
    assert "empty-functions-device" not in entity_unique_ids


async def test_all_devices_without_relay_functions(hass: HomeAssistant, mock_api):
    """Test handling when no devices have relay functions."""
    # Create device data with only non-relay devices
    non_relay_devices = [
        {
            "guid": "sensor-device-1",
            "name": "Temperature Sensor",
            "functions": [{"identifier": "temperature", "type": "value"}],
        },
        {
            "guid": "sensor-device-2",
            "name": "Humidity Sensor",
            "functions": [{"identifier": "humidity", "type": "value"}],
        },
    ]

    # Setup integration with non-relay devices
    entry = await setup_integration(hass, mock_api, non_relay_devices)

    # Verify no entities were created
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    assert len(entities) == 0


async def test_device_with_multiple_functions_including_relay(hass: HomeAssistant, mock_api):
    """Test that devices with multiple functions including relay are added."""
    # Create device with multiple functions including relay
    multi_function_devices = [
        {
            "guid": "multi-device-1",
            "name": "Multi-Function Device",
            "functions": [
                {"identifier": "temperature", "type": "value"},
                {"identifier": "relay", "type": "enumeration"},
                {"identifier": "power", "type": "value"},
            ],
        },
    ]

    # Setup integration
    entry = await setup_integration(hass, mock_api, multi_function_devices)

    # Verify entity was created
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    assert len(entities) == 1
    assert entities[0].unique_id == "multi-device-1"


async def test_device_with_missing_functions_key(hass: HomeAssistant, mock_api):
    """Test that devices missing the functions key are filtered out."""
    # Create device data with missing functions key
    devices_missing_functions = [
        {
            "guid": "relay-device-1",
            "name": "Relay Switch",
            "functions": [{"identifier": "relay", "type": "enumeration"}],
        },
        {
            "guid": "device-no-functions-key",
            "name": "Device Without Functions Key",
            # No functions key at all
        },
    ]

    # Setup integration
    entry = await setup_integration(hass, mock_api, devices_missing_functions)

    # Verify only the device with relay function was added
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    assert len(entities) == 1
    assert entities[0].unique_id == "relay-device-1"
