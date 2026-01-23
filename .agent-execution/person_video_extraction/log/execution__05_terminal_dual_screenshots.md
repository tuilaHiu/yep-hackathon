## [2026-01-23 10:28:00] Task: Dual Screenshots & Larger Window
- **Action:** Update
- **Files Affected:**
  - `app/service/player_selector_terminal.py`
- **Summary:**
  - Re-added `save_detection_screenshot()` function to capture all detected persons
  - Increased preview window size from 1280x720 to **1600x900** for better visibility
  - Automatic saving of **2 screenshots**:
    1. **Detection screenshot** (`*_detected_all_frame*.png`): All persons with RED boxes & IDs - saved immediately after detection
    2. **Selection screenshot** (`*_selected_players_frame*.png`): Only chosen player with GREEN box & name - saved after confirmation
  - Both screenshots save to output directory automatically
- **Verify:**
  - Run `uv run python main.py`
  - Check that window is noticeably larger
  - Verify 2 screenshots are created in output folder
- **Status:** ✅ Success
