---
id: task-16
title: 'https://brands.home-assistant.io/eltako_esr62pf/dark_icon.png is broken'
status: In Progress
assignee: []
created_date: '2025-11-08 07:49'
updated_date: '2025-11-08 07:57'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
This is a custom integration installed via HACS/custom repository, not published to the official Home Assistant brands repository. Therefore, the URL https://brands.home-assistant.io/eltako_esr62pf/dark_icon.png will naturally be broken since the integration isn't in the official brands repo.

For custom integrations, Home Assistant serves icons directly from the local integration folder (custom_components/eltako_esr62pf/). We should add dark theme icon variants to improve the user experience when users have Home Assistant in dark mode.

While the brands.home-assistant.io URL will remain broken (this is normal for custom integrations), having the dark icons locally will ensure they display properly in the Home Assistant UI when dark theme is active.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Create dark_icon.png (256x256) optimized for dark backgrounds
- [ ] #2 Create dark_icon@2x.png (512x512) for high-DPI displays
- [ ] #3 Icons should use transparent or dark background with lighter/contrasting symbol
- [ ] #4 Icons should be properly compressed PNG files
- [ ] #5 Icons should maintain the same visual style as the light theme icons
- [ ] #6 Verify icons are served correctly from the local integration folder in Home Assistant
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### 1. Understand Custom Integration Icon Behavior
- Custom integrations serve icons from `custom_components/{domain}/` directory
- Home Assistant automatically looks for `dark_icon.png` and `dark_icon@2x.png` when in dark mode
- The brands.home-assistant.io URL is only for official integrations in the core repository
- Having local dark icons improves UX for users with dark theme enabled

### 2. Design Dark Theme Variants
Current icon: Blue background (#0066CC) with white symbol (two connected modules)

Options for dark theme:
- **Option A**: Transparent background with lighter blue symbol (recommended for dark mode)
- **Option B**: Darker background with maintained white symbol
- **Option C**: Inverted design

### 3. Create Icon Files
- Generate dark_icon.png (256x256 pixels)
- Generate dark_icon@2x.png (512x512 pixels)
- Place in custom_components/eltako_esr62pf/ alongside existing icons
- Use PNG format with transparency support
- Optimize with lossless compression

### 4. Implementation
- Use Python with PIL/Pillow to create dark variants programmatically
- Maintain the same symbol design as the light icons
- Save in the integration directory
- Keep file sizes reasonable (< 5KB for standard, < 20KB for @2x)

### 5. Testing
- Install/reload the integration in Home Assistant
- Test visibility in Home Assistant dark theme
- Test visibility in Home Assistant light theme (should still use light icons)
- Verify icons are served from local integration folder
<!-- SECTION:PLAN:END -->
