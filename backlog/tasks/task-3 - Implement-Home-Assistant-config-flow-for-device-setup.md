---
id: task-3
title: Implement Home Assistant config flow for device setup
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
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
- [ ] #1 Config flow displays form with IP, Port, and PoP fields
- [ ] #2 IP address input validates IPv4 format
- [ ] #3 Port defaults to 443
- [ ] #4 PoP field is displayed as password input
- [ ] #5 Connection is tested before saving configuration
- [ ] #6 Invalid PoP shows clear error message
- [ ] #7 Network errors show user-friendly error messages
- [ ] #8 SSL certificate errors are handled with clear guidance
- [ ] #9 Multiple devices can be configured independently
- [ ] #10 Credentials are stored securely in config entry
- [ ] #11 strings.json contains all UI text for internationalization
<!-- AC:END -->
