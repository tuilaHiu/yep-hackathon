## [2025-01-15 11:55:00] Task: Implement Court Transform Module
- **Action:** Create
- **Files Affected:**
  - `app/service/court_transform.py`
  - `tests/test_court_transform.py`
- **Summary:** Implemented `CourtTransform` class to handle perspective transformation between pixel coordinates and real-world court meters. Added unit tests to verify corner mapping and round-trip conversion.
- **Verify:** Ran `pytest tests/test_court_transform.py`.
- **Status:** ✅ Success

## [2025-01-15 11:58:00] Task: Fix Import Error in Tests
- **Action:** Create
- **Files Affected:**
  - `conftest.py`
  - `app/__init__.py`
  - `tests/__init__.py`
- **Summary:** Added `conftest.py` to recursively add the project root to `sys.path` during test execution. Created empty `__init__.py` files to ensure packages are recognized.
- **Verify:** Ran `uv run pytest tests/test_court_transform.py` successfully.
- **Status:** ✅ Success
