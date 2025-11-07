---
id: task-5
title: Implement switch platform for relay entities
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
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
- [ ] #1 Switch entities are created for each discovered relay
- [ ] #2 Entity IDs follow naming convention: switch.eltako_{device}_{relay}
- [ ] #3 turn_on service controls relay and updates state optimistically
- [ ] #4 turn_off service controls relay and updates state optimistically
- [ ] #5 toggle service works correctly
- [ ] #6 Unique ID is generated from device GUID
- [ ] #7 Device info includes manufacturer, model, and identifiers
- [ ] #8 State attributes include device_guid, last_updated, connection_status
- [ ] #9 Entities are registered in device and entity registries
- [ ] #10 Entities support area assignment
- [ ] #11 Entity unavailable when device is offline
<!-- AC:END -->
