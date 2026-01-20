# Module Plan: Video Cropping

## 1. Objective
Cắt video gốc theo bounding box của từng người, tạo N video output riêng biệt (N = số người được track).

## 2. Scope
### In-scope
- Đọc tracking data từ module 01
- Crop từng frame theo bounding box
- Pad frame về kích thước cố định (max_bbox + 20%)
- Xuất video riêng cho từng track_id
- Xử lý frame trống khi người không xuất hiện

### Out-of-scope
- Detection/Tracking (handled by module 01)
- Audio extraction (video không cần audio)

## 3. Technical Design

### 3.1 Dependencies
```python
opencv-python>=4.8.0  # Video processing
numpy>=1.24.0         # Array operations
```

### 3.2 File Structure
```
app/service/
├── video_cropper.py       # Main cropping logic
└── output_videos/
    ├── person_1.mp4
    ├── person_2.mp4
    └── ...
```

### 3.3 Cropping Algorithm

```
For each track_id:
  1. Get output_size from tracking_data (max_bbox * 1.2)
  2. Create VideoWriter with output_size
  
  For each frame in video:
    If frame has bbox for this track_id:
      - Crop region from frame
      - Resize/pad to output_size (center aligned)
      - Write to video
    Else:
      - Write black frame (frame trống)
  
  3. Release VideoWriter
```

### 3.4 Padding Strategy
```
┌─────────────────────────────────────┐
│            Black Padding            │
│   ┌─────────────────────────────┐   │
│   │                             │   │
│   │    Cropped Person Image     │   │
│   │                             │   │
│   └─────────────────────────────┘   │
│            Black Padding            │
└─────────────────────────────────────┘
        Output Size (fixed)
```

### 3.5 Implementation Steps

#### Step 1: Create `video_cropper.py`
```python
"""
Video cropping module - Extract individual person videos.
"""
from pathlib import Path
import cv2
import numpy as np
import json

def crop_person_videos(
    video_path: str,
    tracking_data_path: str,
    output_dir: str
) -> list[str]:
    """
    Crop video to extract individual person videos.
    
    Args:
        video_path: Path to original video
        tracking_data_path: Path to tracking JSON from module 01
        output_dir: Directory to save output videos
        
    Returns:
        list[str]: Paths to generated video files
    """
    # Implementation details...
```

#### Step 2: Main Logic Flow
1. Load tracking data from JSON
2. Open source video
3. For each track_id:
   - Create VideoWriter với output_size
   - Loop qua tất cả frames
   - Crop và pad mỗi frame
   - Write frame
   - Release writer
4. Return list of output video paths

#### Step 3: CLI Interface
```bash
python app/service/video_cropper.py \
  --video yep_pickleball.mp4 \
  --tracking app/service/tracking_output/tracking_data.json \
  --output app/service/output_videos/
```

## 4. Deliverables
- [ ] `app/service/video_cropper.py` - Main cropping script
- [ ] `app/service/output_videos/` - Directory với video output
- [ ] Video files: `person_1.mp4`, `person_2.mp4`, ...

## 5. Verification
```bash
# Run cropping
python app/service/video_cropper.py \
  --video yep_pickleball.mp4 \
  --tracking app/service/tracking_output/tracking_data.json

# Verify output
ls -la app/service/output_videos/

# Play video to verify
# ffplay app/service/output_videos/person_1.mp4
```

## 6. Video Output Specs
- **Format:** MP4 (H.264/libx264)
- **FPS:** Same as source video
- **Size:** Fixed (max_bbox_width * 1.2) x (max_bbox_height * 1.2)
- **Naming:** `person_{track_id}.mp4`

## 7. Estimated Effort
- **Time:** 1-2 hours coding
- **Processing:** 5-10 minutes (depends on video length and number of tracks)

## 8. Edge Cases
| Case | Handling |
|------|----------|
| Person not in frame | Write black frame |
| Bbox near edge | Pad with black if crop extends beyond frame |
| Track ID gap | Skip missing IDs, use actual track IDs from data |
| Empty tracking data | Exit with warning, no output |
