---
id: task-3
title: Implement Home Assistant config flow for device setup
status: Done
assignee:
  - Claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:19'
labels:
  - config-flow
  - ui
  - setup
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the configuration flow that allows users to add Eltako ESR62PF-IP devices through the Home Assistant UI. This provides a user-friendly setup experience with validation and error handling.

Config flow requirements:
- UI form with fields: IP Address (IPv4 validation), Port (default 443), PoP credential (password field)
- Username hardcoded as "admin" (not shown to user)
- Connection validation during setup
- Error handling for invalid credentials, network unreachable, SSL errors, API version mismatch
- Support for multiple device instances
- Secure credential storage using HA's config entry system
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Config flow displays form with IP, Port, and PoP fields
- [x] #2 IP address input validates IPv4 format
- [x] #3 Port defaults to 443
- [x] #4 PoP field is displayed as password input
- [x] #5 Connection is tested before saving configuration
- [x] #6 Invalid PoP shows clear error message
- [x] #7 Network errors show user-friendly error messages
- [x] #8 SSL certificate errors are handled with clear guidance
- [x] #9 Multiple devices can be configured independently
- [x] #10 Credentials are stored securely in config entry
- [x] #11 strings.json contains all UI text for internationalization
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan for task-3: Home Assistant Config Flow

### Overview
Implement a Home Assistant config flow that allows users to add Eltako ESR62PF-IP devices through the UI. The flow will handle user input validation, connection testing, error handling, and secure credential storage.

### Key Files to Create/Modify

1. **custom_components/eltako_esr62pf/config_flow.py** (new)
   - Main config flow class inheriting from `config_entries.ConfigFlow`
   - User input form with IP, Port, and PoP fields
   - Connection validation using existing EltakoAPI client
   - Comprehensive error handling

2. **custom_components/eltako_esr62pf/strings.json** (new)
   - UI text and error messages for internationalization
   - Form field labels and descriptions
   - Error messages for various failure scenarios

3. **custom_components/eltako_esr62pf/translations/en.json** (new)
   - English translations (same content as strings.json)

4. **custom_components/eltako_esr62pf/const.py** (modify)
   - Add config flow constants (CONF_IP_ADDRESS, CONF_PORT, CONF_POP_CREDENTIAL)
   - Add error codes for config flow

5. **tests/test_config_flow.py** (new)
   - Comprehensive tests for config flow functionality

### Implementation Steps

1. Update constants in const.py
2. Create config_flow.py with EltakoConfigFlow class
3. Create strings.json with UI text
4. Create translations/en.json
5. Write comprehensive tests in test_config_flow.py
6. Run tests to verify functionality

### Data Schema Design
- IP address: IPv4 validated string
- Port: Integer with default 443, range validation
- PoP credential: Password field

### Error Handling Strategy
- Map EltakoAuthenticationError → "invalid_auth"
- Map EltakoConnectionError → "cannot_connect"
- Map EltakoTimeoutError → "timeout_connect"
- Map SSL errors → "ssl_error"
- Map unknown errors → "unknown"

### Security Considerations
- PoP credential stored in config entry (encrypted by HA)
- Username hardcoded as "admin" (not exposed to user)
- SSL verification disabled by default for self-signed certs
- No credential logging
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Successfully implemented Home Assistant config flow for Eltako ESR62PF-IP devices.

### Files Created:
1. custom_components/eltako_esr62pf/config_flow.py - Main config flow implementation
2. custom_components/eltako_esr62pf/strings.json - UI text and error messages
3. custom_components/eltako_esr62pf/translations/en.json - English translations
4. custom_components/eltako_esr62pf/manifest.json - Integration manifest
5. tests/test_config_flow.py - Comprehensive test suite (15 tests)
6. tests/conftest.py - Test configuration

### Files Modified:
1. custom_components/eltako_esr62pf/const.py - Added config flow constants
2. requirements.txt - Added homeassistant and test dependencies

### Test Results:
All 67 tests passing (52 API tests + 15 config flow tests)
- IPv4 validation working correctly
- Port defaults to 443
- PoP credential field as password input
- Connection validation before config entry creation
- Error handling for authentication, connection, timeout, and SSL errors
- Multiple devices supported with unique IDs
- Credentials stored securely in config entries
- All UI text in strings.json for i18n

### Key Features:
- IPv4 address validation using ipaddress library
- Unique ID generation from IP:Port combination prevents duplicates
- Comprehensive error mapping from API exceptions to user-friendly messages
- Proper resource cleanup (API client closed in finally block)
- Support for multiple independent device configurations
- SSL verification disabled by default for self-signed certificates
<!-- SECTION:NOTES:END -->
