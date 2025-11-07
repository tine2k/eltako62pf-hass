---
id: task-5
title: Implement switch platform for relay entities
status: Done
assignee:
  - Claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:27'
labels:
  - switch
  - entities
  - platform
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the switch platform that exposes Eltako relays as Home Assistant switch entities. Each relay becomes a controllable switch with standard services and state attributes.

Switch entity requirements:
- Extend SwitchEntity from Home Assistant
- Entity naming: switch.eltako_{device_name}_{relay_number}
- Support turn_on, turn_off, and toggle services
- Implement optimistic state updates (assume_state_on_write)
- Unique ID generation from device GUID
- Device registry and entity registry integration
- State attributes: device_guid, last_updated, connection_status
- Area assignment support
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Switch entities are created for each discovered relay
- [x] #2 Entity IDs follow naming convention: switch.eltako_{device}_{relay}
- [x] #3 turn_on service controls relay and updates state optimistically
- [x] #4 turn_off service controls relay and updates state optimistically
- [x] #5 toggle service works correctly
- [x] #6 Unique ID is generated from device GUID
- [x] #7 Device info includes manufacturer, model, and identifiers
- [x] #8 State attributes include device_guid, last_updated, connection_status
- [x] #9 Entities are registered in device and entity registries
- [x] #10 Entities support area assignment
- [x] #11 Entity unavailable when device is offline
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Overview
Create switch.py that implements Home Assistant switch entities for Eltako relays using the existing API client and coordinator.

### Implementation Steps

1. **Create switch platform file** (custom_components/eltako_esr62pf/switch.py)
   - Implement async_setup_entry() to create switch entities from coordinator data
   - Each device from coordinator becomes one switch entity

2. **Implement EltakoSwitchEntity class**
   - Extend SwitchEntity and CoordinatorEntity
   - Properties: unique_id, name, is_on, available, device_info, extra_state_attributes
   - unique_id: Use device GUID
   - name: Extract from device data
   - is_on: Get from coordinator data (device["state"] == "on")
   - available: Based on coordinator's device["available"] flag
   - device_info: manufacturer="Eltako", model="ESR62PF-IP", identifiers from GUID
   - extra_state_attributes: device_guid, last_updated, connection_status

3. **Implement switch control methods**
   - async_turn_on(): Call coordinator.api.async_set_relay(guid, "on") + coordinator.async_set_device_state()
   - async_turn_off(): Call coordinator.api.async_set_relay(guid, "off") + coordinator.async_set_device_state()
   - async_toggle(): Inherited from SwitchEntity base class
   - Error handling: Mark device unavailable on failures using coordinator.async_mark_device_unavailable()

4. **Entity naming convention**
   - Entity ID format: switch.eltako_{sanitized_device_name}
   - For devices without names: switch.eltako_relay_{guid_prefix}
   - Use Home Assistant's slugify utility for sanitization

5. **Integration with device/entity registries**
   - Provide device_info property for automatic device registry
   - Use unique_id for entity registry integration
   - Enables area assignment automatically

### Key Design Decisions
- One entity per device (each GUID = one relay)
- Optimistic updates via coordinator
- Error handling marks entities unavailable
- No state polling in entity (handled by coordinator)

### Files to Create
- custom_components/eltako_esr62pf/switch.py (~150 lines)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implementation completed successfully:
- Created switch.py with EltakoSwitchEntity class extending SwitchEntity and CoordinatorEntity
- Entities are created in async_setup_entry() for each device in coordinator data (AC #1)
- Entity naming uses slugify with 'eltako_' prefix via suggested_object_id (AC #2)
- async_turn_on() implements relay control with optimistic state updates (AC #3)
- async_turn_off() implements relay control with optimistic state updates (AC #4)
- toggle service inherited from SwitchEntity base class (AC #5)
- unique_id property set to device GUID (AC #6)
- device_info property includes manufacturer, model, sw_version, and identifiers (AC #7)
- extra_state_attributes includes device_guid, last_updated, connection_status (AC #8)
- Device registry integration via device_info, entity registry via unique_id (AC #9)
- Area assignment automatically supported through device registry integration (AC #10)
- available property checks coordinator availability and device-specific availability flag (AC #11)
- Error handling marks devices unavailable on API failures
- Python syntax validated successfully
<!-- SECTION:NOTES:END -->
