# Module 03: Selective Tracker

## Owner
`coding_agent`

## Objective
Track chỉ những người chơi đã được user chọn, maintain ID assignment xuyên suốt video bằng cách match với YOLO detections qua IOU.

## Dependencies
- `opencv-python`: Video processing
- `ultralytics`: YOLO detection + ByteTrack
- `numpy`: Array operations, IOU calculation
- Module 01 or 02 output: `selected_players.json`

## Input
- Video file path
- `selected_players.json` từ module 01/02

## Output
- `selective_tracking_data.json`:
```json
{
  "video_info": {
    "source": "yep_pickleball.mp4",
    "fps": 30,
    "total_frames": 9000,
    "width": 1920,
    "height": 1080
  },
  "selected_players": [
    {
      "name": "Nguyen",
      "selection_id": 1,
      "frames": {
        "0": {"x1": 100, "y1": 200, "x2": 200, "y2": 400},
        "1": {"x1": 102, "y1": 198, "x2": 202, "y2": 398},
        ...
      },
      "max_bbox": {"width": 100, "height": 200},
      "output_size": {"width": 120, "height": 240},
      "frame_count": 8500,
      "missing_frames": [50, 51, 52, ...]
    }
  ]
}
```

## Acceptance Criteria
- [ ] Load selected players từ JSON
- [ ] Match initial bbox với YOLO detections để lấy ByteTrack ID
- [ ] Track only selected players throughout video
- [ ] Re-match khi ByteTrack assign new ID (sau occlusion)
- [ ] Record missing frames (khi không detect được)
- [ ] Tính max_bbox và output_size cho mỗi player
- [ ] Progress bar với tqdm

## Technical Design

### 1. Tracking Strategy

```
Frame 0 (Selection Frame):
┌─────────────────────────────────────────┐
│  Selected: Player "Nguyen" at bbox A    │
│  YOLO detect: [det1, det2, det3, det4]  │
│  Match: bbox A ~ det2 → ByteTrack ID=5  │
│  → Track ID 5 = "Nguyen"                │
└─────────────────────────────────────────┘
          ↓
Frame N (Any Frame):
┌─────────────────────────────────────────┐
│  ByteTrack results: [id=5, id=7, id=8]  │
│  → id=5 exists → Record bbox for Nguyen │
│                                         │
│  OR (if id=5 lost):                     │
│  → Re-match using IOU with last bbox    │
│  → New ID 12 best match → 12 = "Nguyen" │
└─────────────────────────────────────────┘
```

### 2. Key Functions

```python
def calculate_iou(box1: dict, box2: dict) -> float:
    """Calculate Intersection over Union between two bboxes."""

def match_bbox_to_detections(
    target_bbox: dict,
    detections: list[dict],
    iou_threshold: float = 0.3
) -> int | None:
    """
    Find best matching detection for target bbox.
    
    Returns:
        int: Index of best match, or None if no good match
    """

def run_selective_tracking(
    video_path: str,
    selected_players_path: str,
    output_path: str | None = None,
    iou_threshold: float = 0.5,
    re_match_interval: int = 30  # Re-match every N frames
) -> dict:
    """
    Track only selected players.
    
    Args:
        video_path: Path to video
        selected_players_path: Path to selected_players.json
        output_path: Path to save tracking data
        iou_threshold: Minimum IOU for matching
        re_match_interval: Frames between re-matching attempts
    
    Returns:
        dict: Tracking data for selected players only
    """
```

### 3. Re-Identification Logic

Khi ByteTrack mất track một người:
1. Lưu last known bbox của người đó
2. Mỗi frame, check các YOLO detections chưa được assign
3. Calculate IOU với last known bbox
4. Nếu IOU > threshold → Re-assign ID mới cho người đó

```python
def handle_lost_track(
    player_name: str,
    last_bbox: dict,
    current_detections: list[dict],
    assigned_track_ids: set[int],
    iou_threshold: float = 0.5
) -> tuple[int | None, dict | None]:
    """
    Try to re-identify a lost player.
    
    Returns:
        tuple: (new_track_id, new_bbox) or (None, None)
    """
```

## File Location
`app/service/selective_tracker.py`

## CLI Usage
```bash
python app/service/selective_tracker.py \
    --video yep_pickleball.mp4 \
    --selected selected_players.json \
    --output selective_tracking_data.json \
    --iou-threshold 0.5
```

## Edge Cases
- Người chưa xuất hiện ở frame đầu → Scan forward đến khi tìm thấy
- Người biến mất hoàn toàn → Record as missing, không crash
- Nhiều người overlap → Ưu tiên IOU cao nhất
- Video ngắn hơn expected → Handle gracefully

## Testing
```python
def test_calculate_iou():
    box1 = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    box2 = {"x1": 50, "y1": 50, "x2": 150, "y2": 150}
    iou = calculate_iou(box1, box2)
    assert 0.14 < iou < 0.15  # Expected ~0.142

def test_match_bbox_to_detections():
    target = {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
    detections = [
        {"x1": 0, "y1": 0, "x2": 50, "y2": 50},      # No overlap
        {"x1": 90, "y1": 90, "x2": 190, "y2": 190},  # High overlap
        {"x1": 150, "y1": 150, "x2": 250, "y2": 250} # Partial
    ]
    result = match_bbox_to_detections(target, detections)
    assert result == 1  # Second detection is best match
```

## Performance Considerations
- Use vectorized NumPy for IOU calculations when possible
- Consider downsampling video for initial scan if too slow
- Cache last N frames of bbox data for re-matching
