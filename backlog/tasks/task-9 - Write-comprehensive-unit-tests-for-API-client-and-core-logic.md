---
id: task-9
title: Write comprehensive unit tests for API client and core logic
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
labels:
  - testing
  - unit-tests
  - api
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Develop unit tests for the API client, authentication, token management, device discovery, and relay control logic. Tests should achieve >80% code coverage for core functionality.

Test coverage areas:
- Authentication with valid/invalid credentials
- Token caching with timestamp tracking
- Token age checking (15-minute threshold)
- Proactive token refresh before API calls
- Reactive token refresh on 401 errors with retry
- Device discovery and parsing
- Relay control commands
- Error scenarios and edge cases
- Retry logic validation
- Self-signed certificate handling
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Test suite uses pytest framework
- [ ] #2 Authentication tests cover valid and invalid credentials
- [ ] #3 Token caching tests verify timestamp storage
- [ ] #4 Token expiry tests verify 15-minute threshold
- [ ] #5 Proactive refresh tests verify token check before API calls
- [ ] #6 401 response tests verify token refresh and retry
- [ ] #7 Device discovery tests cover parsing and caching
- [ ] #8 Relay control tests cover on/off commands
- [ ] #9 Error handling tests cover all custom exceptions
- [ ] #10 Retry logic tests verify exponential backoff
- [ ] #11 Mock HTTP responses for all API interactions
- [ ] #12 Code coverage exceeds 80% for API client
- [ ] #13 Tests run successfully with pytest
<!-- AC:END -->
