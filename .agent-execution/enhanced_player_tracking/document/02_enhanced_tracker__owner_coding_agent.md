# Module 02: Enhanced Tracker

## Owner
`coding_agent`

## Objective
Cập nhật `selective_tracker.py` để sử dụng hybrid matching (Spatial + Color Histogram) thay vì chỉ dùng IOU.

## Dependencies
- Module 01: `app/service/color_histogram.py`
- Existing: `app/service/selective_tracker.py`

## File to Modify
`app/service/selective_tracker.py`

## Changes Overview

### 1. Import color histogram module
```python
from app.service.color_histogram import (
    extract_color_histogram,
    compare_histograms,
    update_histogram_ema,
    crop_bbox_from_frame,
)
```

### 2. Update player_state structure
```python
# Current structure:
player_states.append({
    "name": p["name"],
    "selection_id": p["selection_id"],
    "current_track_id": None,
    "last_bbox": p["initial_bbox"],
    "frames": {},
    "max_bbox": {"width": 0, "height": 0},
    "missing_frames": []
})

# New structure (add reference_histogram):
player_states.append({
    "name": p["name"],
    "selection_id": p["selection_id"],
    "current_track_id": None,
    "last_bbox": p["initial_bbox"],
    "reference_histogram": None,  # NEW: Will be set on first frame
    "frames_lost": 0,             # NEW: Counter for lost track duration
    "frames": {},
    "max_bbox": {"width": 0, "height": 0},
    "missing_frames": []
})
```

### 3. New function: `hybrid_rematch()`

```python
def hybrid_rematch(
    frame: np.ndarray,
    last_bbox: Dict[str, float],
    reference_histogram: np.ndarray,
    frames_lost: int,
    current_detections: List[Dict[str, Any]],
    assigned_track_ids: Set[int],
    base_speed: float = 5.0,
    max_distance_cap: float = 500.0,
    similarity_threshold: float = 0.5,
    distance_weight: float = 0.3,
    histogram_weight: float = 0.7,
) -> Tuple[Optional[int], Optional[Dict[str, float]], Optional[np.ndarray]]:
    """
    Hybrid re-identification using spatial distance + color histogram.
    
    Algorithm:
    1. Calculate max allowed distance based on frames_lost
    2. Filter candidates by center distance
    3. For each candidate, extract histogram and compare
    4. Score = distance_weight * distance_score + histogram_weight * histogram_score
    5. Return best match above threshold
    
    Args:
        frame: Current video frame (BGR).
        last_bbox: Last known bounding box of the player.
        reference_histogram: Reference color histogram of the player.
        frames_lost: Number of frames since track was lost.
        current_detections: List of current YOLO detections.
        assigned_track_ids: Set of track IDs already assigned to other players.
        base_speed: Estimated player speed in pixels per frame.
        max_distance_cap: Maximum search radius in pixels.
        similarity_threshold: Minimum combined score for a valid match.
        distance_weight: Weight for distance score (0-1).
        histogram_weight: Weight for histogram score (0-1).
    
    Returns:
        Tuple of:
            - track_id: New track ID if match found, else None
            - bbox: New bounding box if match found, else None
            - histogram: New histogram if match found (for EMA update), else None
    """
    # Step 1: Calculate max allowed distance
    max_distance = min(base_speed * frames_lost, max_distance_cap)
    
    # Calculate last center
    last_cx = (last_bbox["x1"] + last_bbox["x2"]) / 2
    last_cy = (last_bbox["y1"] + last_bbox["y2"]) / 2
    
    best_score = 0
    best_match = (None, None, None)
    
    for det in current_detections:
        track_id = det.get("track_id")
        if track_id is None or track_id in assigned_track_ids:
            continue
        
        det_bbox = {
            "x1": det["bbox"][0],
            "y1": det["bbox"][1],
            "x2": det["bbox"][2],
            "y2": det["bbox"][3],
        }
        
        # Step 2: Calculate center distance
        det_cx = (det_bbox["x1"] + det_bbox["x2"]) / 2
        det_cy = (det_bbox["y1"] + det_bbox["y2"]) / 2
        distance = ((det_cx - last_cx)**2 + (det_cy - last_cy)**2)**0.5
        
        # Skip if too far
        if distance > max_distance:
            continue
        
        # Step 3: Extract histogram and compare
        det_histogram = extract_color_histogram(frame, det_bbox)
        histogram_similarity = compare_histograms(reference_histogram, det_histogram)
        
        # Normalize histogram similarity to 0-1 range (CORREL returns -1 to 1)
        histogram_score = (histogram_similarity + 1) / 2
        
        # Distance score (1 = close, 0 = far)
        distance_score = 1 - (distance / max_distance)
        
        # Step 4: Combined score
        combined_score = (
            distance_weight * distance_score + 
            histogram_weight * histogram_score
        )
        
        if combined_score > best_score and combined_score >= similarity_threshold:
            best_score = combined_score
            best_match = (track_id, det_bbox, det_histogram)
    
    return best_match
```

### 4. Update tracking loop

```python
# In run_selective_tracking(), modify the main loop:

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run YOLO track
    results = model.track(frame, persist=True, verbose=False)
    
    # Parse detections...
    detections = [...]
    
    assigned_track_ids = set()
    
    # === PASS 1: Update players with active track IDs ===
    for state in player_states:
        if state["current_track_id"] is not None:
            found = False
            for det in detections:
                if det["track_id"] == state["current_track_id"]:
                    # Update bbox
                    bbox_dict = {...}
                    state["frames"][str(frame_idx)] = bbox_dict
                    state["last_bbox"] = bbox_dict
                    state["frames_lost"] = 0  # Reset counter
                    assigned_track_ids.add(state["current_track_id"])
                    
                    # Update reference histogram with EMA
                    if state["reference_histogram"] is not None:
                        new_hist = extract_color_histogram(frame, bbox_dict)
                        state["reference_histogram"] = update_histogram_ema(
                            state["reference_histogram"], 
                            new_hist, 
                            alpha=0.1
                        )
                    
                    found = True
                    break
            
            if not found:
                state["current_track_id"] = None
                state["frames_lost"] += 1
    
    # === PASS 2: Initialize or Re-match lost players ===
    for state in player_states:
        if state["current_track_id"] is None:
            # Initialize histogram on first detection
            if state["reference_histogram"] is None:
                # First time - match by IOU only
                match_idx = match_bbox_to_detections(
                    state["last_bbox"], 
                    detections, 
                    iou_threshold=0.3
                )
                if match_idx is not None:
                    det = detections[match_idx]
                    det_bbox = {...}
                    state["current_track_id"] = det["track_id"]
                    state["last_bbox"] = det_bbox
                    state["frames"][str(frame_idx)] = det_bbox
                    state["frames_lost"] = 0
                    assigned_track_ids.add(det["track_id"])
                    
                    # Extract initial histogram
                    state["reference_histogram"] = extract_color_histogram(
                        frame, det_bbox
                    )
            else:
                # Re-match using hybrid approach
                new_id, new_bbox, new_hist = hybrid_rematch(
                    frame=frame,
                    last_bbox=state["last_bbox"],
                    reference_histogram=state["reference_histogram"],
                    frames_lost=state["frames_lost"],
                    current_detections=detections,
                    assigned_track_ids=assigned_track_ids,
                    base_speed=5.0,
                    max_distance_cap=500.0,
                    similarity_threshold=0.4,
                )
                
                if new_id is not None:
                    state["current_track_id"] = new_id
                    state["last_bbox"] = new_bbox
                    state["frames"][str(frame_idx)] = new_bbox
                    state["frames_lost"] = 0
                    assigned_track_ids.add(new_id)
                    
                    # Update histogram with EMA
                    state["reference_histogram"] = update_histogram_ema(
                        state["reference_histogram"],
                        new_hist,
                        alpha=0.15  # Slightly higher alpha after re-match
                    )
                else:
                    state["frames_lost"] += 1
                    state["missing_frames"].append(frame_idx)
    
    frame_idx += 1
```

### 5. Add new parameters to `run_selective_tracking()`

```python
def run_selective_tracking(
    video_path: str,
    selected_players_path: str,
    output_path: Optional[str] = None,
    iou_threshold: float = 0.5,
    model_path: str = "yolo11n.pt",
    max_frames: Optional[int] = None,
    # NEW parameters:
    base_speed: float = 5.0,
    max_distance_cap: float = 500.0,
    similarity_threshold: float = 0.4,
    histogram_ema_alpha: float = 0.1,
) -> Dict[str, Any]:
    """
    Track only selected players throughout the video.
    
    Args:
        ...existing args...
        base_speed: Estimated player movement speed (pixels/frame).
        max_distance_cap: Maximum search radius for re-matching (pixels).
        similarity_threshold: Minimum score for hybrid matching.
        histogram_ema_alpha: EMA weight for histogram update.
    
    Returns:
        Dict[str, Any]: Tracking data.
    """
```

## Acceptance Criteria

### Core Logic:
- [ ] Reference histogram extracted on first detection
- [ ] Histogram updated with EMA on each tracked frame
- [ ] `hybrid_rematch()` called when track is lost
- [ ] Candidates filtered by distance before histogram comparison
- [ ] Best match selected by combined score

### Integration:
- [ ] Backward compatible - existing CLI still works
- [ ] New parameters exposed in CLI
- [ ] No new dependencies added

### Quality:
- [ ] No "đổi người" in test video
- [ ] Performance <= 20% slower than original
- [ ] Debug logging for re-match events

## Testing

### Manual Test
```bash
# Run with new parameters
python app/service/track_player.py \
    --video yep_pickleball.mp4 \
    --mode terminal \
    --output-dir output_test \
    --base-speed 5.0 \
    --max-distance 500 \
    --similarity-threshold 0.4
```

### Verification Script
```python
# Verify no "ID switch" in output
import json

with open("output_test/selective_tracking_data.json") as f:
    data = json.load(f)

for player in data["selected_players"]:
    frames = player["frames"]
    frame_nums = sorted([int(k) for k in frames.keys()])
    
    # Check for large position jumps (possible wrong re-match)
    jumps = []
    for i in range(1, len(frame_nums)):
        if frame_nums[i] - frame_nums[i-1] == 1:  # Consecutive frames
            prev = frames[str(frame_nums[i-1])]
            curr = frames[str(frame_nums[i])]
            
            prev_cx = (prev["x1"] + prev["x2"]) / 2
            curr_cx = (curr["x1"] + curr["x2"]) / 2
            
            movement = abs(curr_cx - prev_cx)
            if movement > 50:  # Suspicious jump
                jumps.append((frame_nums[i], movement))
    
    print(f"Player {player['name']}: {len(jumps)} suspicious jumps")
    for frame, move in jumps[:5]:
        print(f"  Frame {frame}: {move:.1f}px jump")
```

## Debug Logging

Add logging to track re-match decisions:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In hybrid_rematch():
if best_match[0] is not None:
    logger.info(
        f"Re-matched player: track_id={best_match[0]}, "
        f"score={best_score:.2f}, distance={distance:.1f}px, "
        f"histogram_sim={histogram_similarity:.2f}"
    )
else:
    logger.debug(
        f"No match found. Candidates checked: {len(candidates)}, "
        f"max_distance={max_distance:.1f}px"
    )
```

## Tuning Guide

| Symptom | Parameter to Adjust |
|---------|---------------------|
| Matches wrong person nearby | Increase `histogram_weight`, decrease `distance_weight` |
| Fails to re-match after gap | Increase `base_speed` or `max_distance_cap` |
| Re-matches too aggressively | Increase `similarity_threshold` |
| Histogram drifts over time | Decrease `histogram_ema_alpha` |
| Too sensitive to lighting | Use more bins for Hue, fewer for Saturation |

## CLI Updates

Add new arguments to `app/service/track_player.py`:

```python
parser.add_argument("--base-speed", type=float, default=5.0,
    help="Player movement speed estimate (pixels/frame)")
parser.add_argument("--max-distance", type=float, default=500.0,
    help="Maximum search radius for re-matching (pixels)")
parser.add_argument("--similarity-threshold", type=float, default=0.4,
    help="Minimum score for hybrid matching")
parser.add_argument("--histogram-alpha", type=float, default=0.1,
    help="EMA weight for histogram update")
```
