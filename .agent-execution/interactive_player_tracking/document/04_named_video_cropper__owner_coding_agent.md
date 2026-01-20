# Module 04: Named Video Cropper

## Owner
`coding_agent`

## Objective
Crop video để tạo video riêng cho từng người chơi đã chọn, đặt tên file theo tên người chơi.

## Dependencies
- `opencv-python`: Video processing
- `numpy`: Frame manipulation
- Existing: `app/service/video_cropper.py` (re-use logic)

## Input
- Video file path
- `selective_tracking_data.json` từ module 03

## Output
- Multiple video files: `{player_name}.mp4`
- Example: `Nguyen.mp4`, `Tran.mp4`

## Acceptance Criteria
- [ ] Đọc tracking data từ module 03
- [ ] Crop video cho từng người được chọn
- [ ] Output size = max_bbox + 20% padding
- [ ] Frame đen khi người không xuất hiện (missing frames)
- [ ] Tên file = tên người chơi (sanitized)
- [ ] Cùng FPS với video gốc
- [ ] Progress bar cho mỗi video

## Technical Design

### 1. Reuse Existing Code

Module này có thể **extend** hoặc **wrap** `video_cropper.py` hiện có:

```python
# Option A: Modify existing video_cropper.py
# Thêm parameter để accept named players

# Option B: Create wrapper (Recommended)
# named_video_cropper.py imports và sử dụng functions từ video_cropper.py
```

### 2. Key Functions

```python
def sanitize_filename(name: str) -> str:
    """
    Convert player name to safe filename.
    
    Examples:
        "Nguyen Van A" -> "nguyen_van_a"
        "Player #1" -> "player_1"
        "Trần" -> "tran"
    """

def crop_named_player_videos(
    video_path: str,
    tracking_data_path: str,
    output_dir: str | None = None,
    include_black_frames: bool = True
) -> list[str]:
    """
    Crop video for each named player.
    
    Args:
        video_path: Path to source video
        tracking_data_path: Path to selective_tracking_data.json
        output_dir: Output directory
        include_black_frames: If True, write black frames when player missing
    
    Returns:
        list[str]: Paths to generated video files
    """
```

### 3. Black Frame Handling

```python
# Current video_cropper.py logic (skip missing frames):
if frame_str in track_data["frames"]:
    cropped = crop_and_pad_frame(frame, bbox, output_size)
    writer.write(cropped)

# New logic (include black frames):
if frame_str in track_data["frames"]:
    cropped = crop_and_pad_frame(frame, bbox, output_size)
    writer.write(cropped)
else:
    black_frame = create_black_frame(output_size)
    writer.write(black_frame)
```

### 4. Filename Sanitization Rules

| Input | Output |
|-------|--------|
| `Nguyen` | `nguyen.mp4` |
| `Nguyen Van A` | `nguyen_van_a.mp4` |
| `Player #1` | `player_1.mp4` |
| `Trần Văn B` | `tran_van_b.mp4` (diacritics removed) |
| `123abc` | `123abc.mp4` |
| `!!!` | `player_unknown.mp4` (fallback) |

## File Location
`app/service/named_video_cropper.py`

## CLI Usage
```bash
python app/service/named_video_cropper.py \
    --video yep_pickleball.mp4 \
    --tracking selective_tracking_data.json \
    --output output_videos/ \
    --include-black-frames
```

## Edge Cases
- Tên trùng nhau → Thêm suffix `_1`, `_2`
- Tên chứa ký tự đặc biệt → Sanitize
- Tracking data empty → Error message, không crash
- Video không mở được → FileNotFoundError

## Testing
```python
def test_sanitize_filename():
    assert sanitize_filename("Nguyen") == "nguyen"
    assert sanitize_filename("Nguyen Van A") == "nguyen_van_a"
    assert sanitize_filename("Player #1") == "player_1"
    assert sanitize_filename("!!!") == "player_unknown"

def test_crop_named_player_videos():
    # Integration test với sample data
    pass
```

## Integration with video_cropper.py

Có thể import và reuse các functions:
```python
from app.service.video_cropper import (
    crop_and_pad_frame,
    create_black_frame,
    load_tracking_data,
)
```
