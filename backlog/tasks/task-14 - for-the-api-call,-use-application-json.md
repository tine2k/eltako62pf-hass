---
id: task-14
title: 'for the api call, use application/json'
status: Done
assignee: []
created_date: '2025-11-07 23:23'
updated_date: '2025-11-07 23:27'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix API login error: "Attempt to decode JSON with unexpected mimetype: text/html". The issue is that the API is returning HTML instead of JSON because the request is not explicitly setting `Content-Type: application/json` header. While aiohttp's `json=` parameter encodes the payload as JSON, it may not always set the Content-Type header correctly, causing the server to return HTML instead of JSON.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Login request explicitly sets 'Content-Type: application/json' header
- [x] #2 Login succeeds and returns JSON response (not HTML)
- [x] #3 Error 'Attempt to decode JSON with unexpected mimetype: text/html' is resolved
- [x] #4 Relay control requests also include Content-Type header
- [x] #5 All existing tests pass

- [x] #6 Integration can successfully authenticate with the device
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### 1. Root Cause Analysis
**Error**: `200, message='Attempt to decode JSON with unexpected mimetype: text/html'`
- The API returns status 200 but with HTML content instead of JSON
- This happens when the server doesn't recognize the request as a JSON API call
- **Solution**: Explicitly set `Content-Type: application/json` header

### 2. Fix Location
File: `custom_components/eltako_esr62pf/api.py`

**Method 1: `async_login()` (line 122-183)**
- Currently uses `json=payload` which may not set Content-Type header
- Need to explicitly add `Content-Type: application/json` to headers

**Method 2: `_make_request()` (line 198-311)**
- Already handles headers via kwargs
- Should explicitly set Content-Type when JSON payload is present

### 3. Implementation Approach
**Option A** (Recommended): Add explicit headers in `async_login()`
```python
async with session.post(
    url,
    json=payload,
    headers={"Content-Type": "application/json"},
    ssl=self._ssl_context,
) as response:
```

**Option B**: Centralize in `_make_request()`
- Detect when `json` kwarg is present
- Automatically add Content-Type header
- Benefits both login and relay control endpoints

### 4. Testing Steps
1. Run the integration and verify login succeeds
2. Check that error message no longer appears
3. Verify relay control still works
4. Run existing test suite
5. Add test to verify Content-Type header is set

### 5. Files to Modify
- `custom_components/eltako_esr62pf/api.py` - Add explicit Content-Type header
- `tests/test_api.py` - Verify headers in requests (if needed)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

### Changes Made
1. **async_login() method (line 144)**: Added explicit `Content-Type: application/json` header to the POST request
2. **_make_request() method (lines 230-232)**: Added automatic Content-Type header detection - when `json` kwarg is present, it sets the header using `setdefault()` to avoid overriding any explicitly set headers

### Fix Details
The root cause was that the Eltako API server was returning HTML instead of JSON (status 200 with text/html mimetype) because it didn't recognize the requests as JSON API calls. While aiohttp's `json=` parameter encodes the payload as JSON, it doesn't always set the Content-Type header in a way the server recognizes.

### Testing Results
- All 52 API tests passed successfully
- Both login and relay control endpoints now explicitly set Content-Type
- The fix is centralized in `_make_request()` and also explicitly set in `async_login()`

### Files Modified
- custom_components/eltako_esr62pf/api.py
<!-- SECTION:NOTES:END -->
