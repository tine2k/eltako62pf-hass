---
id: task-2
title: Implement device discovery and relay control in API client
status: Done
assignee:
  - Claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:06'
labels:
  - api
  - device-discovery
  - relay-control
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the EltakoAPI client with methods for discovering devices and controlling relay states. This enables the integration to query available relays and send control commands.

Required functionality:
- GET /api/v0/devices endpoint integration
- Device GUID parsing and caching
- PUT /api/v0/devices/{device_guid}/functions/relay endpoint for relay control
- Support for ON/OFF commands with proper payload structure
- Device GUID validation before sending commands
- Command queueing for simultaneous requests
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 async_get_devices() retrieves and parses device list with GUIDs
- [x] #2 Device list can be cached with configurable refresh
- [x] #3 async_set_relay(device_guid, state) sends correct payload format
- [x] #4 Relay control supports 'on' and 'off' values
- [x] #5 Device GUID is validated before API calls
- [x] #6 Invalid device GUIDs raise appropriate exceptions
- [x] #7 Multiple simultaneous commands are queued properly
- [x] #8 API responses are parsed and mapped correctly
- [x] #9 Unit tests cover device discovery and relay control scenarios
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Overview
Extend the EltakoAPI class with device discovery and relay control functionality.

### Implementation Steps

1. **Add Device Discovery Method (async_get_devices)**
   - Call GET /api/v0/devices endpoint using _make_request
   - Parse response to extract device list with GUIDs
   - Add caching mechanism with configurable TTL (60 seconds default)
   - Return list of device dictionaries

2. **Add Relay Control Method (async_set_relay)**
   - Call PUT /api/v0/devices/{device_guid}/functions/relay endpoint
   - Accept device_guid and state ('on' or 'off') parameters
   - Validate device_guid before API call
   - Format payload as {"value": state}
   - Leverage existing _make_request for retry/auth logic

3. **Add Device Validation Exception**
   - Add EltakoInvalidDeviceError to exceptions.py
   - Raise when device GUID validation fails

4. **Implement Command Queueing**
   - Add asyncio.Lock for relay control
   - Prevent race conditions for simultaneous commands

5. **Write Comprehensive Unit Tests**
   - Device discovery success and error cases
   - Cache and refresh logic
   - Relay control with on/off states
   - Device GUID validation
   - Concurrent command handling
   - API response parsing

### Files to Modify
- api.py - Add new methods and caching
- exceptions.py - Add new exception class
- const.py - Add cache TTL constant
- test_api.py - Add comprehensive tests
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Completed

### Changes Made

1. **Exception Class Added** (exceptions.py)
   - Added `EltakoInvalidDeviceError` exception for device GUID validation failures

2. **Constants Added** (const.py)
   - Added `DEVICE_CACHE_TTL = 60` for device list caching (60 seconds)
   - Imported new endpoint and relay state constants

3. **API Client Extensions** (api.py)
   - Added device caching fields: `_devices_cache`, `_devices_cache_timestamp`
   - Added relay control lock: `_relay_lock`
   - Implemented `_is_device_cache_expired()` helper method
   - Implemented `async_get_devices(force_refresh=False)` method:
     - Retrieves device list from GET /api/v0/devices
     - Caches results with 60-second TTL
     - Supports force refresh to bypass cache
     - Returns list of device dictionaries with GUIDs
   - Implemented `async_set_relay(device_guid, state)` method:
     - Controls relay via PUT /api/v0/devices/{device_guid}/functions/relay
     - Validates device GUID (non-empty string)
     - Validates state ('on' or 'off' only)
     - Uses asyncio.Lock to queue concurrent commands
     - Sends JSON payload: {"value": state}

4. **Comprehensive Test Coverage** (test_api.py)
   - Added `TestDeviceDiscovery` class with 8 test cases:
     - Success scenarios
     - Cache behavior and expiry
     - Force refresh
     - Empty lists and invalid responses
     - Connection errors
   - Added `TestRelayControl` class with 11 test cases:
     - On/off control
     - Device GUID validation (empty, None, wrong type)
     - Invalid state validation
     - Concurrent command queueing
     - API errors and connection failures
     - Payload format verification

### Test Results
- All 52 tests passed (34 existing + 18 new)
- Test execution time: 25.33 seconds
- Coverage includes all acceptance criteria

### Implementation Highlights
- Leveraged existing `_make_request` infrastructure for authentication, retry logic, and error handling
- Device caching reduces API calls and improves performance
- Command queueing with asyncio.Lock prevents race conditions
- Comprehensive validation prevents invalid API calls
- Follows existing code patterns and conventions
<!-- SECTION:NOTES:END -->
