---
id: task-4
title: Implement data update coordinator with optional polling
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
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
- [ ] #1 Coordinator extends DataUpdateCoordinator properly
- [ ] #2 Polling is disabled by default (update_interval = None)
- [ ] #3 Optimistic updates work without polling enabled
- [ ] #4 When polling enabled, update_interval respects configured value
- [ ] #5 Minimum polling interval of 10 seconds is enforced
- [ ] #6 Coordinator fetches device states when polling is active
- [ ] #7 Failed updates mark entities as unavailable
- [ ] #8 Connection errors trigger graceful degradation
- [ ] #9 Coordinator supports multiple switch entities
- [ ] #10 State data is properly distributed to all entities
<!-- AC:END -->
