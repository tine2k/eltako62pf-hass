---
id: task-1
title: Implement Eltako API client with authentication and token management
status: Done
assignee:
  - Claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 21:56'
labels:
  - api
  - authentication
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the core API client class (EltakoAPI) that handles all HTTP communication with the Eltako ESR62PF-IP device. This includes authentication, token lifecycle management, and retry logic.

The API client must handle:
- HTTPS communication with self-signed certificate support
- Login endpoint with hardcoded username "admin" and user-provided PoP credential
- API token caching with 15-minute TTL
- Proactive token refresh checking age before each API call
- Reactive token refresh on 401 responses with single retry
- Thread-safe token access
- Exponential backoff retry logic (max 3 attempts)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 async_login() authenticates and returns API key
- [x] #2 API key is cached with creation timestamp
- [x] #3 _is_token_expired() correctly checks 15-minute threshold
- [x] #4 _ensure_valid_token() refreshes expired tokens before API calls
- [x] #5 401 responses trigger token refresh and single retry
- [x] #6 Self-signed certificates are accepted when configured
- [x] #7 Failed requests implement exponential backoff (max 3 retries)
- [x] #8 All methods are async and thread-safe
- [x] #9 No credentials are logged in any mode
- [x] #10 Unit tests cover authentication, token caching, expiry, and refresh scenarios
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan: Eltako API Client

### 1. Project Structure Setup
- Create `custom_components/eltako_esr62pf/` directory structure
- Create `api.py` for the API client implementation
- Create `exceptions.py` for custom exception classes
- Create `const.py` for constants (URLs, timeouts, token TTL, etc.)

### 2. Exception Classes (`exceptions.py`)
Define custom exceptions:
- `EltakoAuthenticationError` - Authentication failures
- `EltakoConnectionError` - Network/connection issues
- `EltakoAPIError` - General API errors
- `EltakoTimeoutError` - Request timeout errors

### 3. Constants (`const.py`)
Define key constants:
- `API_TOKEN_TTL = 900` (15 minutes in seconds)
- `MAX_RETRIES = 3`
- `RETRY_BACKOFF_BASE = 2` (exponential backoff)
- `DEFAULT_TIMEOUT = 10`
- API endpoint paths

### 4. Core API Client Class (`api.py`)
**Initialization:**
- `__init__(ip_address, pop_credential, port=443, verify_ssl=True, session=None)`
- Initialize aiohttp ClientSession with SSL context
- Set up token cache and timestamp
- Initialize asyncio Lock for thread-safe operations

**Authentication:**
- `async_login()` - POST to `/api/v0/login` with username "admin" and PoP
- Cache API key with timestamp

**Token Management:**
- `_is_token_expired()` - Check 15-minute threshold
- `_ensure_valid_token()` - Refresh if expired before API calls
- Use asyncio Lock for thread safety

**HTTP Request Wrapper:**
- `_make_request()` - Centralized request handler
- Call `_ensure_valid_token()` before each request
- Exponential backoff retry (max 3 attempts)
- Handle 401: refresh token once and retry
- Never log credentials

### 5. Implementation Order
1. Create directory structure
2. Implement exceptions.py
3. Implement const.py
4. Implement api.py (EltakoAPI class)
5. Write unit tests
6. Verify all acceptance criteria
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete

### Files Created:
1. `custom_components/eltako_esr62pf/exceptions.py` - Custom exception classes
2. `custom_components/eltako_esr62pf/const.py` - Constants and configuration
3. `custom_components/eltako_esr62pf/api.py` - Core API client (125 lines)
4. `custom_components/eltako_esr62pf/__init__.py` - Integration entry point
5. `tests/test_api.py` - Comprehensive unit tests (34 tests)
6. `requirements.txt` - Python dependencies
7. `pytest.ini` - Test configuration

### Test Results:
- **34 tests passed** (100% pass rate)
- **95% code coverage** on api.py
- All acceptance criteria met

### Key Features Implemented:
- ✅ async_login() with API key caching and timestamp
- ✅ Token expiry detection (15-minute threshold)
- ✅ Proactive token refresh before API calls
- ✅ Reactive 401 handling with token refresh and retry
- ✅ SSL certificate support (configurable verification)
- ✅ Exponential backoff retry logic (max 3 retries)
- ✅ Thread-safe token management with asyncio.Lock
- ✅ Credential sanitization in logs
- ✅ Comprehensive error handling
- ✅ Context manager support

### Code Quality:
- Type hints throughout
- Clear docstrings
- Follows Home Assistant patterns
- Clean separation of concerns
<!-- SECTION:NOTES:END -->
