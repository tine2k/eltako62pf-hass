---
id: task-10
title: Write integration tests for Home Assistant components
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
labels:
  - testing
  - integration-tests
  - home-assistant
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Develop integration tests that verify the complete setup flow, entity creation, state updates, polling configuration, and integration with Home Assistant core.

Integration test coverage:
- Full config flow setup with validation
- Options flow for polling configuration
- Entity creation and registration
- Switch service calls (turn_on, turn_off, toggle)
- Optimistic state updates without polling
- State synchronization with polling enabled
- State behavior with polling disabled
- Network error simulation and recovery
- Re-authentication flow
- Integration reload and unload
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Config flow test creates integration with valid credentials
- [ ] #2 Config flow test rejects invalid credentials
- [ ] #3 Options flow test updates polling configuration
- [ ] #4 Entity creation test verifies all relays are discovered
- [ ] #5 Service call tests verify turn_on/turn_off/toggle work
- [ ] #6 Optimistic update test verifies immediate state changes
- [ ] #7 Polling enabled test verifies periodic state updates
- [ ] #8 Polling disabled test verifies no background updates
- [ ] #9 Network error test verifies graceful degradation
- [ ] #10 Re-authentication test verifies automatic token refresh
- [ ] #11 Integration reload test verifies clean unload/reload
- [ ] #12 Tests use pytest-homeassistant-custom-component
- [ ] #13 All integration tests pass successfully
<!-- AC:END -->
