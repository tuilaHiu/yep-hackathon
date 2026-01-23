## [2026-01-23 09:35:35] Task: Add Screenshot Capture on Player Selection
- **Action:** Update
- **Files Affected:**
  - `app/service/player_selector_terminal.py`
  - `app/service/player_selector_gui.py`
- **Summary:** 
  Added `save_selection_screenshot()` function to both player selector modules. When a player is selected, the system now automatically captures and saves an annotated screenshot showing:
  - Green bounding boxes around selected players
  - Player names with labels
  - Frame index and timestamp
  - Screenshot is saved as PNG in the output directory
  - Path is added to the JSON result as `screenshot_path`
- **Verify:** 
  ```bash
  python main.py --video pickleball.mp4 --output-dir output
  # Check for PNG file in output directory
  ```
- **Status:** ✅ Success
