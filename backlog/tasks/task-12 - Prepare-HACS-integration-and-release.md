---
id: task-12
title: Prepare HACS integration and release
status: To Do
assignee: []
created_date: '2025-11-07 21:48'
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
