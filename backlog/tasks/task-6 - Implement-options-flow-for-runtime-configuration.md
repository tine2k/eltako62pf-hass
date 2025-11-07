---
id: task-6
title: Implement options flow for runtime configuration
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
labels:
  - options-flow
  - ui
  - configuration
  - eltako
  - mvp
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create the options flow that allows users to reconfigure integration settings without removing and re-adding the device. This includes updating the PoP credential and configuring the polling interval.

Options flow features:
- Update PoP credential field
- Enable/disable polling checkbox
- Polling interval input (min 10 seconds, recommended 30-60 seconds)
- Display current polling status
- Validate and save configuration
- Trigger coordinator update with new settings
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Options flow is accessible from integration settings
- [ ] #2 PoP credential can be updated
- [ ] #3 Enable/disable polling checkbox is present
- [ ] #4 Polling interval field enforces minimum of 10 seconds
- [ ] #5 Current polling status is displayed clearly
- [ ] #6 Validation prevents invalid configurations
- [ ] #7 Changes are saved to config entry
- [ ] #8 Coordinator is updated with new polling interval
- [ ] #9 Re-authentication occurs if PoP is changed
- [ ] #10 UI text matches PRD specification in strings.json
<!-- AC:END -->
