## [2026-01-20 11:18:00] Task: Selective Tracker Implementation
- **Action:** Create
- **Files Affected:**
  - `app/service/selective_tracker.py`
  - `tests/test_selective_tracker.py`
- **Summary:** Implemented a selective tracking service using YOLOv11 and IOU-based re-matching. The service follows only user-selected players and records their movement, handling track ID changes and missing frames. Added unit tests for IOU and matching logic.
- **Verify:** `uv run pytest tests/test_selective_tracker.py` and `uv run python app/service/selective_tracker.py --video yep_pickleball.mp4 --selected test_terminal_selection.json --output selective_tracking_data.json --max-frames 50`
- **Status:** ✅ Success
