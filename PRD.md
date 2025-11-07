# Product Requirements Document: Eltako ESR62PF-IP Home Assistant Integration

## 1. Executive Summary

### 1.1 Purpose
This document defines the requirements for a Home Assistant custom integration that enables control and monitoring of Eltako ESR62PF-IP relay devices through the Home Assistant platform.

### 1.2 Product Overview
The Eltako ESR62PF-IP is a network-connected relay control device that provides remote switching capabilities. This integration will allow Home Assistant users to control relays, monitor device status, and automate operations through the Home Assistant ecosystem.

### 1.3 Target Users
- Home Assistant users with Eltako ESR62PF-IP devices
- Smart home enthusiasts integrating Eltako building automation
- Professional installers deploying Eltako solutions in smart buildings

## 2. Product Goals

### 2.1 Primary Goals
1. Enable seamless control of Eltako ESR62PF-IP relays from Home Assistant
2. Provide automatic device discovery and configuration
3. Support real-time status updates and state synchronization
4. Ensure reliability and error handling for production environments

### 2.2 Success Metrics
- Integration listed in HACS (Home Assistant Community Store)
- Support for all relay control functions
- < 500ms response time for relay operations
- Zero data loss during normal operations
- Clear error messages and recovery mechanisms

## 3. Technical Requirements

### 3.1 API Integration

#### 3.1.1 Authentication
- **Endpoint**: `https://{ip_address}:443/api/v0/login`
- **Method**: POST
- **Requirements**:
  - Fixed username "admin" (hardcoded, not user-configurable)
  - Accept PoP (Proof of Possession) value from user
  - Secure storage of API keys after authentication
  - API key validity: 15 minutes
  - Cache API key with timestamp
  - Token refresh strategy:
    - Check token age before each API call
    - If token is older than 15 minutes, refresh before making the API call
    - If API returns 401 Unauthorized, refresh token and retry the request once
    - No automatic background token refresh
  - Handle self-signed SSL certificates (rejectUnauthorized support)

#### 3.1.2 Device Discovery
- **Endpoint**: `https://{ip_address}:443/api/v0/devices`
- **Method**: GET
- **Requirements**:
  - Retrieve all connected devices on integration setup
  - Parse device GUID for each relay
  - Support dynamic device addition/removal
  - Cache device list with configurable refresh interval

#### 3.1.3 Relay Control
- **Endpoint**: `https://{ip_address}:443/api/v0/devices/{device_guid}/functions/relay`
- **Method**: PUT
- **Requirements**:
  - Support ON/OFF commands
  - Include API key in Authorization header
  - Validate device GUID before sending commands
  - Handle command queueing for multiple simultaneous requests
  - Payload structure:
    ```json
    {
      "type": "enumeration",
      "identifier": "relay",
      "value": "on" | "off"
    }
    ```

### 3.2 Home Assistant Platform Requirements

#### 3.2.1 Configuration Flow
- **Config Flow Implementation**:
  - User-friendly UI-based setup
  - Fields required:
    - IP Address (validation for IPv4 format)
    - Port (default: 443)
    - PoP (Proof of Possession) - authentication credential
  - Username is hardcoded as "admin" (not visible/configurable by user)
  - Connection validation during setup
  - Error handling for:
    - Invalid PoP credential
    - Network unreachable
    - SSL certificate errors
    - API version mismatch

#### 3.2.2 Integration Components
- **Switch Platform**: Primary entity for relay control
  - Entity naming: `switch.eltako_{device_name}_{relay_number}`
  - Support for standard switch services:
    - `switch.turn_on`
    - `switch.turn_off`
    - `switch.toggle`
  - State attributes:
    - `device_guid`: Unique device identifier
    - `last_updated`: Timestamp of last state change
    - `connection_status`: Online/Offline

#### 3.2.3 Entity Features
- Unique ID generation based on device GUID
- Device registry integration
- Entity registry integration
- Support for device areas assignment
- Entity customization support

### 3.3 Data Management

#### 3.3.1 State Synchronization
- Optimistic updates for user commands (state updates immediately in UI)
- Polling for device state is **disabled by default**
- Polling interval is user-configurable via Options Flow
  - Default: Disabled (0 or null)
  - When enabled: Recommended interval 30-60 seconds
  - Minimum interval: 10 seconds (to prevent excessive API calls)
- State reconciliation occurs on poll interval (when enabled)
- Webhook support for push updates (future enhancement)

#### 3.3.2 Error Handling
- Retry logic for failed API calls (exponential backoff)
- Maximum 3 retry attempts before marking offline
- Graceful degradation on communication errors
- User notifications for persistent errors
- Recovery mechanisms:
  - Automatic reconnection on network restoration
  - Re-authentication on token expiry

### 3.4 Security Requirements
- Secure credential storage using Home Assistant's storage
- HTTPS enforcement for all API communications
- Support for self-signed certificates with user warning
- No credential logging in debug mode
- API key rotation support

## 4. Functional Requirements

### 4.1 Core Features (MVP)

#### F1: Device Configuration
- **Priority**: P0
- **Description**: Allow users to add Eltako ESR62PF-IP devices via config flow
- **Acceptance Criteria**:
  - User can enter IP, port, and PoP credential
  - Username "admin" is used automatically (not user-configurable)
  - Integration validates credentials before saving
  - Configuration is stored securely
  - Multiple devices can be configured

#### F2: Relay Control
- **Priority**: P0
- **Description**: Control relay states through Home Assistant
- **Acceptance Criteria**:
  - Relays appear as switch entities
  - Turn on/off commands work reliably
  - State changes reflect in UI within 2 seconds
  - Toggle function works correctly

#### F3: Status Monitoring
- **Priority**: P0
- **Description**: Display current relay states
- **Acceptance Criteria**:
  - Current state is accurate
  - State updates on polling interval
  - Connection status visible in device info
  - Entity unavailable when device offline

#### F4: Device Discovery
- **Priority**: P0
- **Description**: Automatically discover all relays on the device
- **Acceptance Criteria**:
  - All relays discovered on setup
  - Each relay creates a separate entity
  - Device information populated correctly

### 4.2 Enhanced Features (Post-MVP)

#### F5: Options Flow
- **Priority**: P0 (moved from P1 - required for polling configuration)
- **Description**: Allow reconfiguration without removing integration
- **Features**:
  - Update PoP credential
  - Configure polling interval (default: disabled)
    - Option to disable polling (0/null)
    - Option to enable with custom interval (min: 10 seconds, recommended: 30-60 seconds)
  - Configure timeout values
  - Enable/disable specific relays

#### F6: Diagnostics
- **Priority**: P1
- **Description**: Provide diagnostic information for troubleshooting
- **Features**:
  - Connection diagnostics
  - API response logging
  - Device information export
  - Integration health status

#### F7: Service Calls
- **Priority**: P2
- **Description**: Custom services for advanced control
- **Features**:
  - `eltako.refresh_devices`: Force device list refresh
  - `eltako.reconnect`: Force reconnection
  - Pulse control (timed on/off)

#### F8: Notifications
- **Priority**: P2
- **Description**: Integration events and alerts
- **Features**:
  - Connection lost notifications
  - Device added/removed events
  - API errors as persistent notifications

## 5. Non-Functional Requirements

### 5.1 Performance
- API response time: < 500ms under normal conditions
- Startup time: < 10 seconds for integration load
- Memory footprint: < 50MB per device
- CPU usage: < 5% during normal operations

### 5.2 Reliability
- 99.9% uptime when network is available
- Automatic recovery from temporary network issues
- No data corruption on unexpected shutdown
- State persistence across restarts

### 5.3 Compatibility
- Home Assistant Core 2024.1.0 or later
- Python 3.11 or later
- Support for Home Assistant OS, Container, Core installations
- IPv4 networking support

### 5.4 Maintainability
- Code coverage > 80%
- Type hints for all public functions
- Documentation for all public APIs
- Follow Home Assistant development standards

### 5.5 Usability
- Setup completion in < 2 minutes
- Clear error messages in user's language
- Consistent with Home Assistant UI patterns
- Comprehensive documentation

## 6. User Interface Requirements

### 6.1 Configuration Flow UI
```
Step 1: Device Connection
┌─────────────────────────────────────┐
│ Configure Eltako ESR62PF-IP        │
├─────────────────────────────────────┤
│ IP Address: [____________]          │
│ Port:       [443________]           │
│ PoP:        [************]          │
│                                     │
│ Note: Username is fixed as "admin"  │
│                                     │
│         [Cancel]  [Submit]          │
└─────────────────────────────────────┘

Step 2: Device Selection (if multiple relays)
┌─────────────────────────────────────┐
│ Select Relays to Add                │
├─────────────────────────────────────┤
│ ☑ Relay 1 - Living Room            │
│ ☑ Relay 2 - Kitchen                │
│ ☑ Relay 3 - Bedroom                │
│                                     │
│         [Cancel]  [Continue]        │
└─────────────────────────────────────┘
```

### 6.2 Options Flow UI
```
Configure Options
┌─────────────────────────────────────┐
│ Eltako ESR62PF-IP Options          │
├─────────────────────────────────────┤
│ PoP:        [************]          │
│                                     │
│ Polling Interval (seconds):         │
│ ☐ Enable polling                    │
│   [30_______] (min: 10)            │
│                                     │
│ Note: Polling is disabled by        │
│ default. Enable only if you need    │
│ state synchronization with external │
│ device changes.                     │
│                                     │
│         [Cancel]  [Submit]          │
└─────────────────────────────────────┘
```

### 6.3 Entity Card Display
- Standard switch card with on/off toggle
- Device name and relay identifier
- Connection status indicator
- Last updated timestamp (only when polling is enabled)

### 6.4 Device Info Page
- Device manufacturer: "Eltako"
- Device model: "ESR62PF-IP"
- Firmware version (if available)
- IP address
- Connection status
- Number of configured relays
- Polling status: "Enabled (30s)" or "Disabled"

## 7. Integration Architecture

### 7.1 Component Structure
```
custom_components/eltako_esr62pf/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── config_flow.py        # Configuration UI
├── const.py             # Constants
├── coordinator.py       # Data update coordinator
├── switch.py            # Switch platform
├── api.py               # API client
├── exceptions.py        # Custom exceptions
└── strings.json         # UI strings
```

### 7.2 Data Flow
```
User Action → Switch Entity → Coordinator → API Client → Device
                    ↓
            State Update → Entity State
```

### 7.3 Key Classes

#### EltakoAPI
- Handles all HTTP communication
- Manages authentication and session
- Implements retry logic
- Token caching and lifecycle management:
  - Caches API key with creation timestamp
  - Checks token age before each API call (15-minute threshold)
  - Refreshes expired tokens before API calls
  - Handles 401 responses by refreshing token and retrying once
  - Thread-safe token access
- Methods:
  - `async_login()` - Authenticate and get new API key
  - `async_get_devices()` - Get device list
  - `async_set_relay(device_guid, state)` - Control relay state
  - `_is_token_expired()` - Internal method to check token age
  - `_ensure_valid_token()` - Internal method to refresh if needed before API calls

#### EltakoDataUpdateCoordinator
- Extends `DataUpdateCoordinator`
- Manages optional polling and state updates
- Polling behavior:
  - Disabled by default (no automatic polling)
  - Update interval configurable via Options Flow
  - Only polls when explicitly enabled by user
- Handles connection lifecycle
- Provides data to entities
- Supports optimistic state updates (immediate UI feedback)

#### EltakoSwitch
- Extends `SwitchEntity`
- Represents individual relay
- Implements turn_on/turn_off
- Provides state and attributes

## 8. Testing Requirements

### 8.1 Unit Tests
- API client authentication
- Token caching with timestamp
- Token age checking (15-minute threshold)
- Token refresh before API call when expired
- Reactive token refresh on 401 errors with retry
- Relay control commands
- State parsing and mapping
- Error handling scenarios
- Retry logic validation

### 8.2 Integration Tests
- Full setup flow
- Entity creation and registration
- Optimistic state updates (immediate UI feedback)
- Optional polling configuration (disabled by default)
- State updates with polling enabled
- State updates with polling disabled
- Network error simulation
- Re-authentication flow

### 8.3 Manual Test Cases
1. Initial setup with valid credentials
2. Initial setup with invalid credentials
3. Control relay from Home Assistant UI (verify optimistic update)
4. Verify state updates after manual device control (with polling disabled - state should remain optimistic)
5. Enable polling via Options Flow and verify state synchronization
6. Disable polling via Options Flow and verify no background updates
7. Configure custom polling interval (e.g., 30 seconds) and verify update frequency
8. Network disconnection and recovery
9. Multiple simultaneous commands
10. Integration reload
11. Home Assistant restart
12. Token expiration handling (wait 15+ minutes, then trigger action - should refresh token)
13. Multiple API calls reusing cached token (within 15 minutes - should not re-authenticate)
14. 401 response handling (simulate expired token, verify retry with fresh token)

## 9. Documentation Requirements

### 9.1 README.md
- Integration overview
- Features list
- Installation instructions
- Configuration guide
- Troubleshooting section
- Known limitations

### 9.2 Installation Guide
- HACS installation (preferred)
- Manual installation steps
- Verification steps

### 9.3 Configuration Documentation
- Required parameters
- Optional parameters
- Example configurations
- Advanced options

### 9.4 API Documentation
- Supported services
- Service call examples
- Automation examples
- Event documentation

## 10. Deployment and Release

### 10.1 Release Criteria
- All P0 features implemented
- Test coverage > 80%
- Documentation complete
- HACS validation passed
- No known critical bugs

### 10.2 Version Numbering
- Semantic versioning (MAJOR.MINOR.PATCH)
- Initial release: 1.0.0

### 10.3 Distribution
- GitHub repository
- HACS custom repository
- Future: Official Home Assistant integration

## 11. Future Enhancements

### 11.1 Phase 2 Features
- Energy monitoring (if supported by device)
- Scene support
- Webhook support for instant updates
- Multiple device support in single integration instance

### 11.2 Phase 3 Features
- Device firmware updates through HA
- Advanced diagnostics and logging
- Integration with Eltako cloud services (if available)
- Support for other Eltako IP devices

## 12. Risks and Mitigations

### 12.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API changes by manufacturer | High | Medium | Version detection, graceful degradation |
| Self-signed certificate issues | Medium | High | Clear user documentation, certificate validation options |
| Network latency | Medium | Medium | Configurable timeouts, async operations |
| Concurrent access conflicts | Medium | Low | Command queueing, state locking |

### 12.2 Project Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Limited device access for testing | High | High | Community testing, emulator development |
| API documentation incomplete | Medium | Medium | Reverse engineering, community collaboration |
| Home Assistant API changes | Medium | Medium | Follow HA development, version pinning |

## 13. Dependencies

### 13.1 Python Libraries
- `aiohttp`: Async HTTP client
- `asyncio`: Async operations
- Standard library only for core functionality

### 13.2 Home Assistant Components
- `homeassistant.config_entries`
- `homeassistant.helpers.entity`
- `homeassistant.helpers.update_coordinator`
- `homeassistant.components.switch`

### 13.3 Development Tools
- `pytest`: Testing framework
- `pytest-homeassistant-custom-component`: HA testing utilities
- `black`: Code formatting
- `pylint`: Code linting
- `mypy`: Type checking

## 14. Acceptance Criteria

### 14.1 MVP Acceptance
- [ ] User can add device through UI configuration
- [ ] All relays discovered and added as switch entities
- [ ] Switch entities can be turned on/off
- [ ] Optimistic state updates work correctly (immediate UI feedback)
- [ ] Polling is disabled by default
- [ ] Options Flow allows configuring polling interval
- [ ] State synchronization works when polling is enabled
- [ ] Integration handles network disconnection gracefully
- [ ] Documentation is complete and accurate
- [ ] Code passes all linting and type checks
- [ ] Test coverage > 80%

### 14.2 Production Ready
- [ ] Integration tested with real hardware
- [ ] HACS validation passed
- [ ] Community testing completed
- [ ] Known issues documented
- [ ] Support channels established

## 15. Appendix

### 15.1 API Reference

#### Login API
```http
POST https://{ip_address}:443/api/v0/login
Content-Type: application/json

{
  "user": "admin",
  "password": "{POP_VALUE}"
}

Response:
{
  "apiKey": "xxxxx-xxxxx-xxxxx"
}
```

#### Get Devices API
```http
GET https://{ip_address}:443/api/v0/devices
Authorization: {apiKey}

Response:
[
  {
    "deviceGuid": "xxxx-xxxx-xxxx",
    ...
  }
]
```

#### Control Relay API
```http
PUT https://{ip_address}:443/api/v0/devices/{device_guid}/functions/relay
Authorization: {apiKey}
Content-Type: application/json

{
  "type": "enumeration",
  "identifier": "relay",
  "value": "on"
}
```

### 15.2 Glossary
- **PoP**: Proof of Possession - Authentication credential specific to the Eltako device
- **GUID**: Globally Unique Identifier - Device identifier
- **HACS**: Home Assistant Community Store
- **API Key**: Authentication token returned after login (valid for 15 minutes)
- **Token TTL**: Time To Live - 15 minutes for API keys
- **Coordinator**: Home Assistant pattern for managing data updates

### 15.3 References
- Home Assistant Developer Documentation: https://developers.home-assistant.io/
- Eltako ESR62PF-IP API Specification: https://www.eltako.com/fileadmin/downloads/de/_bedienung/flowbr62ip.json
- HACS Documentation: https://hacs.xyz/

---

**Document Version**: 1.4
**Last Updated**: 2025-11-07
**Status**: Draft
**Owner**: Development Team
**Changelog**:
- v1.4: Polling disabled by default, configurable via Options Flow (P0 priority), optimistic updates
- v1.3: Updated token refresh strategy - check age before API calls, no automatic background refresh, retry on 401
- v1.2: Added API token caching requirement (15-minute TTL with proactive refresh)
- v1.1: Removed username field from configuration (hardcoded as "admin"), renamed Password to PoP in user-facing contexts
- v1.0: Initial version
