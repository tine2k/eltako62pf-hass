---
id: task-12
title: Prepare HACS integration and release
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
updated_date: '2025-11-07 22:37'
labels:
  - hacs
  - distribution
  - release
  - eltako
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prepare the integration for distribution via HACS (Home Assistant Community Store), ensuring all metadata, validation requirements, and release artifacts are in place.

HACS preparation:
- Validate manifest.json meets HACS requirements
- Create hacs.json configuration file
- Set up GitHub repository with proper structure
- Create release with version tags
- Prepare info.md for HACS listing
- Validate with HACS action/validator
- Submit to HACS default repository (if desired)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 manifest.json passes HACS validation
- [ ] #2 hacs.json is created with correct configuration
- [ ] #3 GitHub repository has proper structure and tags
- [ ] #4 Release 1.0.0 is created with proper semver
- [ ] #5 info.md provides clear integration description
- [ ] #6 HACS validator action passes
- [ ] #7 Installation via HACS custom repository works
- [ ] #8 All release artifacts are included
- [ ] #9 Version numbering follows semantic versioning
- [ ] #10 Release notes document all features and known issues
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Phase 1: HACS Requirements Analysis (COMPLETED)
**Objective:** Understand all HACS requirements for custom integrations

**Key Findings:**
- Repository must contain single integration in `custom_components/INTEGRATION_NAME/`
- Manifest.json MUST have: domain, documentation, issue_tracker, codeowners, name, version
- hacs.json required in repository root
- GitHub releases with semantic versioning preferred
- Integration must be added to home-assistant/brands repository
- Public GitHub repository with descriptive README required

**Current Status:**
- ✓ Correct folder structure: `custom_components/eltako_esr62pf/`
- ✓ Has domain, documentation, name, version in manifest.json
- ✗ MISSING: issue_tracker in manifest.json
- ✗ MISSING: codeowners has empty array (needs at least one owner)
- ✗ MISSING: hacs.json file
- ✗ MISSING: README.md file
- ✗ MISSING: info.md for HACS listing
- ✗ MISSING: GitHub releases with tags

### Phase 2: Manifest.json Enhancement
**Tasks:**
1. Add `issue_tracker` field pointing to GitHub issues URL
2. Add at least one codeowner (GitHub username)
3. Validate all required fields are present
4. Ensure documentation URL is correct

**Required manifest.json fields per HACS:**
- domain ✓
- documentation ✓
- issue_tracker ✗
- codeowners ✗ (empty)
- name ✓
- version ✓

### Phase 3: Create HACS Configuration Files
**Tasks:**
1. Create `hacs.json` in repository root with:
   - name: "Eltako ESR62PF-IP"
   - homeassistant: minimum version requirement
   - Optional: content_in_root, persistent_directory

2. Create `README.md` with:
   - Project description
   - Features list
   - Installation instructions (HACS + manual)
   - Configuration guide
   - Usage examples
   - Known limitations
   - Links to documentation

3. Create `info.md` for HACS listing with:
   - Brief description
   - Installation instructions
   - Basic configuration steps
   - Links to full documentation

### Phase 4: GitHub Actions Validation
**Tasks:**
1. Create `.github/workflows/hacs-validation.yml`
2. Use HACS action to validate repository structure
3. Validate manifest.json
4. Run on pull requests and pushes to main

### Phase 5: Repository Verification
**Tasks:**
1. Verify folder structure: `custom_components/eltako_esr62pf/`
2. Confirm all required files present
3. Validate manifest.json against HACS requirements
4. Check README completeness
5. Ensure GitHub repository has:
   - Descriptive repository description
   - Relevant topics/tags
   - MIT or compatible license

### Phase 6: Release Creation
**Tasks:**
1. Create annotated git tag: `v1.0.0`
2. Create GitHub release with:
   - Tag: v1.0.0
   - Title: "Release 1.0.0"
   - Release notes including:
     - Features list
     - Installation instructions
     - Known issues
     - Breaking changes (if any)
3. Ensure semantic versioning is followed

### Phase 7: Testing
**Tasks:**
1. Test installation via HACS custom repository
2. Verify integration appears in HACS UI
3. Test installation process
4. Verify integration loads correctly
5. Test uninstall/reinstall flow

### Phase 8: Optional - Submit to HACS Default Repository
**Tasks:**
1. Ensure all validation passes
2. Add integration to home-assistant/brands repository
3. Submit PR to HACS default repository
4. Address any review feedback

## Technical Details

### Minimum Home Assistant Version
Based on the code review, we should require:
- Home Assistant >= 2024.1.0 (for modern config flow and entity features)

### HACS.json Configuration
```json
{
  "name": "Eltako ESR62PF-IP",
  "homeassistant": "2024.1.0"
}
```

### Required Manifest.json Changes
```json
{
  "domain": "eltako_esr62pf",
  "name": "Eltako ESR62PF-IP",
  "codeowners": ["@tine2k"],
  "config_flow": true,
  "documentation": "https://github.com/tine2k/eltako62pf-hass",
  "issue_tracker": "https://github.com/tine2k/eltako62pf-hass/issues",
  "integration_type": "device",
  "iot_class": "local_polling",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0"
}
```

### Repository Structure Validation
```
eltako62pf-hass/
├── .github/
│   └── workflows/
│       └── hacs-validation.yml
├── custom_components/
│   └── eltako_esr62pf/
│       ├── __init__.py
│       ├── api.py
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── manifest.json
│       ├── strings.json
│       ├── switch.py
│       └── translations/
│           └── en.json
├── tests/
├── backlog/
├── hacs.json
├── info.md
├── README.md
├── LICENSE
└── requirements.txt
```

## Dependencies

**Prerequisite Tasks:**
- task-8: Error handling (recommended before release)
- task-9: Unit tests (recommended for quality)
- task-10: Integration tests (recommended for stability)
- task-11: Documentation (required for README)

**Blocked By:**
- None (can proceed independently)

**Blocks:**
- Final release and distribution

## Risk Assessment

**Low Risk:**
- Creating hacs.json
- Creating README.md and info.md
- GitHub Actions workflow

**Medium Risk:**
- Manifest.json changes (could break integration if incorrect)
- Release tagging (needs to be done correctly)

**Mitigation:**
- Test manifest changes locally before committing
- Validate JSON syntax
- Follow semantic versioning strictly
- Test HACS installation in development environment

## Success Criteria

1. ✓ All HACS validation checks pass
2. ✓ Integration installs successfully via HACS custom repository
3. ✓ manifest.json has all required fields
4. ✓ hacs.json is properly configured
5. ✓ README.md is comprehensive and clear
6. ✓ Release v1.0.0 is created with proper tags
7. ✓ GitHub Actions workflow validates repository
8. ✓ All acceptance criteria marked as complete
<!-- SECTION:PLAN:END -->
