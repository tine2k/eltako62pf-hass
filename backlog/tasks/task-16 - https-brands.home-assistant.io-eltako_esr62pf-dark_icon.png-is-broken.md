---
id: task-16
title: 'https://brands.home-assistant.io/eltako_esr62pf/dark_icon.png is broken'
status: Done
assignee: []
created_date: '2025-11-08 07:49'
updated_date: '2025-11-08 07:59'
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
- [x] #1 Create dark_icon.png (256x256) optimized for dark backgrounds
- [x] #2 Create dark_icon@2x.png (512x512) for high-DPI displays
- [x] #3 Icons should use transparent or dark background with lighter/contrasting symbol
- [x] #4 Icons should be properly compressed PNG files
- [x] #5 Icons should maintain the same visual style as the light theme icons
- [x] #6 Verify icons are served correctly from the local integration folder in Home Assistant
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Details

### Icons Created
- `dark_icon.png`: 256x256px, 1.4KB
- `dark_icon@2x.png`: 512x512px, 3.1KB

### Design Approach
Used a lighter blue color (#6699FF) instead of the original dark blue (#0066CC) to ensure good visibility on dark backgrounds. The icons maintain the same symbol design (two connected module shapes) with white symbols on the lighter blue circular background.

### Technical Details
- Format: PNG with RGBA (8-bit/color)
- Compression: Optimized with PIL/Pillow
- Transparency: Full RGBA support
- File sizes: Reasonable and smaller than light theme variants

### Files
- Script: [create_dark_icons.py](create_dark_icons.py)
- Icons: [dark_icon.png](custom_components/eltako_esr62pf/dark_icon.png), [dark_icon@2x.png](custom_components/eltako_esr62pf/dark_icon@2x.png)
<!-- SECTION:NOTES:END -->
