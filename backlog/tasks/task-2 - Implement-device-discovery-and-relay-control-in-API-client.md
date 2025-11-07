---
id: task-2
title: Implement device discovery and relay control in API client
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
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
- [ ] #1 async_get_devices() retrieves and parses device list with GUIDs
- [ ] #2 Device list can be cached with configurable refresh
- [ ] #3 async_set_relay(device_guid, state) sends correct payload format
- [ ] #4 Relay control supports 'on' and 'off' values
- [ ] #5 Device GUID is validated before API calls
- [ ] #6 Invalid device GUIDs raise appropriate exceptions
- [ ] #7 Multiple simultaneous commands are queued properly
- [ ] #8 API responses are parsed and mapped correctly
- [ ] #9 Unit tests cover device discovery and relay control scenarios
<!-- AC:END -->
