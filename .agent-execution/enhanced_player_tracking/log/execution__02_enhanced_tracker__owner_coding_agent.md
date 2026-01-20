## [2026-01-20 15:25:00] Task: Enhanced Player Tracking Implementation
- **Action:** Update
- **Files Affected:**
  - `app/service/selective_tracker.py`
  - `app/service/track_player.py`
- **Summary:** Implemented hybrid re-matching using spatial distance and color histograms in `selective_tracker.py`. Updated `track_player.py` to expose and pass new tracking parameters. Added EMA-based histogram updates for robust tracking.
- **Verify:** Run `python app/service/track_player.py --video yep_pickleball.mp4 --mode terminal --max-players 1` and check logs for re-match events.
- **Status:** ✅ Success
