---
id: task-6
title: Implement options flow for runtime configuration
status: Done
assignee:
  - claude
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:32'
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
- [x] #1 Options flow is accessible from integration settings
- [x] #2 PoP credential can be updated
- [x] #3 Enable/disable polling checkbox is present
- [x] #4 Polling interval field enforces minimum of 10 seconds
- [x] #5 Current polling status is displayed clearly
- [x] #6 Validation prevents invalid configurations
- [x] #7 Changes are saved to config entry
- [x] #8 Coordinator is updated with new polling interval
- [x] #9 Re-authentication occurs if PoP is changed
- [x] #10 UI text matches PRD specification in strings.json
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan for Task-6: Options Flow

### Overview
Implement a Home Assistant options flow to allow runtime reconfiguration of the integration without requiring removal and re-addition. This will enable users to update the PoP credential and configure polling settings.

### Key Files to Modify
1. config_flow.py - Add OptionsFlowHandler class
2. __init__.py - Add options update listener
3. strings.json - Add options flow UI strings
4. translations/en.json - Mirror strings.json content

### Implementation Steps

1. Add Options Flow Handler to config_flow.py
   - Create OptionsFlowHandler class inheriting from config_entries.OptionsFlow
   - Implement async_step_init() method to display options form
   - Create schema with PoP credential, enable polling checkbox, polling interval field
   - Implement validation logic (test auth, validate interval >= 10 seconds)
   - Return async_create_entry() to save options

2. Register Options Flow in ConfigFlow
   - Add @staticmethod method async_get_options_flow() to EltakoConfigFlow class
   - Return instance of OptionsFlowHandler

3. Add Options Update Listener in __init__.py
   - Create async_update_options() listener function
   - Register listener in async_setup_entry()
   - Handle PoP credential changes (re-authenticate)
   - Handle polling interval changes (update coordinator)
   - Use hass.config_entries.async_reload() to apply changes

4. Update UI Strings in strings.json
   - Add options section with step title, descriptions, field labels
   - Add error messages and data descriptions

5. Update translations/en.json
   - Mirror all strings.json content

### Technical Considerations
- Re-authentication when PoP changes (update entry.data)
- Dynamic polling interval updates on coordinator
- Conditional UI for polling interval field
- Reuse existing validation from config flow
- Preserve config if validation fails
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implementation completed successfully:

1. Created EltakoOptionsFlowHandler class in config_flow.py with async_step_init() method
2. Registered options flow in EltakoConfigFlow via async_get_options_flow() static method
3. Added async_update_options() listener in __init__.py that reloads the config entry when options change
4. Updated strings.json with complete options flow UI text including:
   - Step title and description
   - Field labels (pop_credential, enable_polling, poll_interval)
   - Data descriptions with recommendations
   - Error messages including invalid_poll_interval
5. Mirrored all content to translations/en.json

Technical implementation details:
- Options flow validates PoP credential by testing authentication if changed
- Updates config entry.data when PoP changes (triggers re-authentication on reload)
- Saves polling settings to entry.options
- Enforces minimum polling interval of 10 seconds with validation
- Uses conditional schema to show poll_interval field
- Reuses existing error handling from config flow
- Integration reloads via async_update_options listener when options change
- Coordinator automatically picks up new polling interval on reload (via entry.options)

All acceptance criteria verified and Python syntax validated.
<!-- SECTION:NOTES:END -->
