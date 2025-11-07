---
id: task-4
title: Implement data update coordinator with optional polling
status: Done
assignee:
  - Claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:24'
labels:
  - coordinator
  - polling
  - state-management
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the EltakoDataUpdateCoordinator that manages state updates and optional polling for relay devices. By default, polling is disabled and the coordinator relies on optimistic updates. Users can enable polling via Options Flow.

Coordinator responsibilities:
- Extend DataUpdateCoordinator from Home Assistant
- Support optimistic state updates (immediate UI feedback)
- Polling disabled by default (update_interval = None)
- Configurable polling interval via Options Flow (min 10 seconds, recommended 30-60)
- Coordinate API calls and state distribution to entities
- Handle connection lifecycle and error states
- Provide data to switch entities
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Coordinator extends DataUpdateCoordinator properly
- [x] #2 Polling is disabled by default (update_interval = None)
- [x] #3 Optimistic updates work without polling enabled
- [x] #4 When polling enabled, update_interval respects configured value
- [x] #5 Minimum polling interval of 10 seconds is enforced
- [x] #6 Coordinator fetches device states when polling is active
- [x] #7 Failed updates mark entities as unavailable
- [x] #8 Connection errors trigger graceful degradation
- [x] #9 Coordinator supports multiple switch entities
- [x] #10 State data is properly distributed to all entities
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan for task-4: Data Update Coordinator

### Overview
Create `coordinator.py` that implements the `EltakoDataUpdateCoordinator` class, managing device state updates with optional polling support.

### Key Design Decisions

1. **Polling Architecture**
   - Default: `update_interval = None` (no polling)
   - Optimistic updates: Switch entities update state immediately on commands
   - Optional polling: Configurable via Options Flow (task-6)
   - Minimum interval: 10 seconds (enforced)

2. **Data Structure**
   - Coordinator data will be a dict mapping device GUIDs to their states
   - Format: `{device_guid: {"state": "on"/"off", "available": bool}}`

3. **Integration Points**
   - Used by `__init__.py` in `async_setup_entry()`
   - Provides data to switch entities (task-5)
   - Configured by Options Flow (task-6)

### Implementation Steps

1. **Create coordinator.py file**
   - Location: `custom_components/eltako_esr62pf/coordinator.py`

2. **Define EltakoDataUpdateCoordinator class**
   - Extend `DataUpdateCoordinator[dict[str, Any]]`
   - Constructor parameters: hass, api, update_interval (None default)
   - Store API client reference
   - Initialize with proper logger

3. **Implement `_async_update_data()` method**
   - Called automatically when polling is enabled
   - Fetch device states via `api.async_get_devices()`
   - Transform API response to coordinator data format
   - Handle errors and raise `UpdateFailed`
   - Return device state dictionary

4. **Add method for optimistic state updates**
   - `async def async_set_device_state(device_guid: str, state: str) -> None`
   - Updates coordinator data immediately without API call
   - Triggers entity updates via `async_set_updated_data()`

5. **Add constants to const.py**
   - CONF_POLL_INTERVAL, MIN_POLL_INTERVAL, DEFAULT_POLL_INTERVAL

6. **Update __init__.py**
   - Create coordinator in `async_setup_entry()`
   - Store in hass.data, load switch platform
   - Cleanup in `async_unload_entry()`

7. **Error Handling**
   - UpdateFailed for polling errors
   - Graceful degradation with last known state

### Files to Create/Modify
- New: `coordinator.py`
- Modified: `__init__.py`, `const.py`
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implementation completed successfully. All acceptance criteria verified through static checks and imports.

Created coordinator.py with EltakoDataUpdateCoordinator class extending DataUpdateCoordinator

Implemented polling with default update_interval=None (polling disabled by default)

Added async_set_device_state() for optimistic updates

Added async_mark_device_unavailable() for error handling

Implemented _async_update_data() with comprehensive error handling (UpdateFailed exceptions)

Added polling constants: MIN_POLL_INTERVAL=10s, DEFAULT_POLL_INTERVAL=30s, CONF_POLL_INTERVAL config key

Updated __init__.py to create coordinator in async_setup_entry with options support

Implemented proper cleanup in async_unload_entry (API close, data cleanup)

Data structure: dict[device_guid: {state, available, name, guid}] supports multiple devices

Verified all imports and syntax successful
<!-- SECTION:NOTES:END -->
