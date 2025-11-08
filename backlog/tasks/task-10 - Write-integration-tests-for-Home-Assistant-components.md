---
id: task-10
title: Write integration tests for Home Assistant components
status: Done
assignee: []
created_date: '2025-11-07 21:48'
updated_date: '2025-11-08 07:21'
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
- [x] #1 Config flow test creates integration with valid credentials
- [x] #2 Config flow test rejects invalid credentials
- [x] #3 Options flow test updates polling configuration
- [x] #4 Entity creation test verifies all relays are discovered
- [x] #5 Service call tests verify turn_on/turn_off/toggle work
- [x] #6 Optimistic update test verifies immediate state changes
- [x] #7 Polling enabled test verifies periodic state updates
- [x] #8 Polling disabled test verifies no background updates
- [x] #9 Network error test verifies graceful degradation
- [x] #10 Re-authentication test verifies automatic token refresh
- [x] #11 Integration reload test verifies clean unload/reload
- [x] #12 Tests use pytest-homeassistant-custom-component
- [x] #13 All integration tests pass successfully
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan for Integration Tests

### 1. **Setup Test Infrastructure** (Phase 1)
- Create `tests/test_integration.py` file
- Set up pytest fixtures for Home Assistant testing
  - Use `pytest-homeassistant-custom-component` plugin (already configured)
  - Create mock API client fixture
  - Create mock device data fixtures
- Set up test helpers for:
  - Config entry creation
  - Entity verification
  - State updates

### 2. **Config Flow Integration Tests** (Phase 2)
Tests to verify the complete setup flow:

**Test: Full config flow setup with validation**
- Initialize config flow
- Provide valid credentials
- Verify entry is created with correct data
- Verify coordinator is set up
- Verify entities are created

**Test: Config flow rejects invalid credentials**
- Initialize config flow
- Provide invalid credentials
- Verify authentication error is shown
- Verify no entry is created

### 3. **Options Flow Integration Tests** (Phase 3)
Tests for polling configuration:

**Test: Options flow updates polling configuration**
- Create existing config entry
- Open options flow
- Enable polling with specific interval
- Verify integration reloads
- Verify polling is active

**Test: Options flow disables polling**
- Create entry with polling enabled
- Open options flow
- Disable polling
- Verify integration reloads
- Verify polling is disabled

### 4. **Entity Creation and Registration Tests** (Phase 4)
Tests for entity lifecycle:

**Test: Entity creation verifies all relays are discovered**
- Mock API to return multiple devices
- Set up integration
- Verify correct number of switch entities created
- Verify each entity has correct attributes
- Verify entity IDs are correct
- Verify device registry entries

### 5. **Service Call Tests** (Phase 5)
Tests for switch.turn_on, turn_off, and toggle:

**Test: Turn on service call**
- Create switch entity
- Call turn_on service
- Verify API method called
- Verify state updated optimistically
- Verify entity state is "on"

**Test: Turn off service call**
- Create switch entity (initially on)
- Call turn_off service
- Verify API method called
- Verify state updated optimistically
- Verify entity state is "off"

**Test: Toggle service call**
- Create switch entity (known state)
- Call toggle service
- Verify state toggles correctly
- Verify API called with correct state

### 6. **Optimistic Update Tests** (Phase 6)
Tests for immediate state updates without polling:

**Test: Optimistic update without polling**
- Set up integration with polling disabled
- Turn on a switch
- Verify state updates immediately
- Verify no polling occurred
- Verify UI reflects change

**Test: Optimistic updates are instant**
- Measure time between service call and state update
- Verify update happens before any network round-trip

### 7. **Polling Tests** (Phase 7)
Tests for periodic state synchronization:

**Test: Polling enabled updates state periodically**
- Set up integration with 10-second polling
- Mock API to return changed states
- Wait for poll interval
- Verify coordinator fetched new data
- Verify entity states updated

**Test: Polling disabled prevents background updates**
- Set up integration without polling
- Wait for extended period
- Verify no automatic API calls made
- Verify state only changes on service calls

### 8. **Network Error and Recovery Tests** (Phase 8)
Tests for error handling:

**Test: Network error simulation**
- Set up working integration
- Simulate network error (connection refused)
- Attempt switch operation
- Verify graceful error handling
- Verify entity marked unavailable
- Verify persistent notification shown

**Test: Recovery from network errors**
- Start with failed state (3+ consecutive failures)
- Restore network connectivity
- Make successful API call
- Verify entities marked available
- Verify notification cleared
- Verify normal operation resumed

**Test: Timeout handling**
- Simulate API timeout
- Verify timeout error caught
- Verify retry mechanism works
- Verify appropriate error shown

### 9. **Re-authentication Tests** (Phase 9)
Tests for token refresh:

**Test: Automatic token refresh**
- Set up integration with expired token
- Make API call that requires re-auth
- Verify automatic re-authentication
- Verify operation succeeds
- Verify no user intervention needed

**Test: Failed re-authentication**
- Simulate invalid credentials on refresh
- Verify error notification
- Verify entities marked unavailable

### 10. **Integration Reload and Unload Tests** (Phase 10)
Tests for lifecycle management:

**Test: Clean integration reload**
- Set up integration
- Create entities
- Reload integration
- Verify old entities removed
- Verify new entities created
- Verify state preserved where appropriate

**Test: Clean integration unload**
- Set up integration
- Unload integration
- Verify entities removed
- Verify API client closed
- Verify coordinator cleaned up
- Verify no resource leaks

### 11. **Test Utilities and Helpers** (Common)
Create reusable test utilities:
- `create_mock_api()` - Returns mock EltakoAPI
- `create_mock_devices()` - Returns test device data
- `setup_integration()` - Helper to set up integration in tests
- `assert_entity_state()` - Helper to verify entity state
- `simulate_network_error()` - Helper to inject errors
- `wait_for_state_change()` - Async helper for state verification

### 12. **Documentation and Test Organization**
- Group tests by category (config flow, entities, services, etc.)
- Use descriptive test names
- Add docstrings explaining what each test validates
- Use pytest markers for test categorization
- Ensure all tests are independent and can run in any order

### Success Criteria
✓ All 13 acceptance criteria passing
✓ Test coverage for all major code paths
✓ Tests are fast and reliable
✓ No flaky tests
✓ Clear test output and error messages
✓ Integration with pytest-homeassistant-custom-component
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Successfully implemented comprehensive integration tests for the Home Assistant components.

### Test File Created
- `tests/test_integration.py` - 19 integration tests covering all acceptance criteria

### Test Coverage
1. **Config Flow Tests** (2 tests)
   - Full integration setup with valid credentials
   - Invalid credentials rejection

2. **Options Flow Tests** (2 tests)
   - Enable polling configuration
   - Disable polling configuration

3. **Entity Creation Tests** (1 test)
   - All discovered devices create switch entities
   - Entity registry verification
   - Device attributes validation

4. **Service Call Tests** (3 tests)
   - turn_on service
   - turn_off service
   - toggle service

5. **Optimistic Update Tests** (2 tests)
   - Immediate state changes without polling
   - No background polling when disabled

6. **Polling Tests** (2 tests)
   - Periodic updates when enabled
   - No automatic updates when disabled

7. **Error Handling Tests** (3 tests)
   - Network error graceful degradation
   - Recovery from multiple failures
   - Timeout error handling

8. **Re-authentication Tests** (2 tests)
   - Automatic token refresh behavior
   - Failed re-authentication handling

9. **Integration Lifecycle Tests** (2 tests)
   - Clean integration reload
   - Clean integration unload with resource cleanup

### Test Results
- **Total Tests**: 101 (52 API tests + 13 config flow tests + 17 error handling tests + 19 integration tests)
- **Pass Rate**: 100% (101/101 passing)
- **Test Framework**: pytest with pytest-homeassistant-custom-component

### Code Changes
- Fixed `switch.py:194` to use `hasattr()` check for `last_update_success_time` attribute
- Removed obsolete `_validate_ipv4` tests from `test_config_flow.py`

### Key Testing Patterns Used
- Mock API fixtures for isolation
- Async test helpers for Home Assistant integration
- Entity registry verification
- State machine validation
- Error injection and recovery testing
- Lifecycle management verification

All acceptance criteria met. Integration tests provide comprehensive coverage of the Home Assistant integration functionality.
<!-- SECTION:NOTES:END -->
