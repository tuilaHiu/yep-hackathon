# Module Plan: Person Tracking Detection

## 1. Objective
Detect và track tất cả người trong video `yep_pickleball.mp4` bằng YOLO + ByteTrack, xuất tracking data để module tiếp theo sử dụng.

## 2. Scope
### In-scope
- Load video input
- Chạy YOLOv8 detection cho class "person"
- Áp dụng ByteTrack để assign persistent track ID
- Lưu tracking data vào JSON file
- Tính toán max bounding box cho mỗi track_id

### Out-of-scope
- Crop video (handled by module 02)
- GUI/visualization (optional debug only)

## 3. Technical Design

### 3.1 Dependencies
```python
# Đã có trong pyproject.toml
ultralytics>=8.4.2  # YOLO + ByteTrack built-in

# Cần thêm
opencv-python>=4.8.0
```

### 3.2 File Structure
```
app/service/
├── person_tracker.py      # Main tracking logic
└── tracking_output/
    └── tracking_data.json # Output tracking data
```

### 3.3 Tracking Data Schema
```json
{
  "video_info": {
    "source": "yep_pickleball.mp4",
    "fps": 30,
    "total_frames": 1800,
    "width": 1920,
    "height": 1080
  },
  "tracks": {
    "1": {
      "max_bbox": {"width": 150, "height": 300},
      "output_size": {"width": 180, "height": 360},
      "frames": {
        "0": {"x1": 100, "y1": 200, "x2": 250, "y2": 500},
        "1": {"x1": 102, "y1": 198, "x2": 252, "y2": 498},
        ...
      }
    },
    "2": { ... }
  }
}
```

### 3.4 Implementation Steps

#### Step 1: Create `person_tracker.py`
```python
"""
Person detection and tracking module using YOLO + ByteTrack.
"""
from pathlib import Path
from ultralytics import YOLO
import cv2
import json

def run_tracking(video_path: str, output_dir: str) -> dict:
    """
    Run YOLO detection with ByteTrack on video.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save tracking data
        
    Returns:
        dict: Tracking data with video info and all tracks
    """
    # Implementation details...
```

#### Step 2: Main Logic Flow
1. Load YOLO model (`yolov8n.pt` hoặc `yolov8s.pt`)
2. Open video với OpenCV
3. Loop qua từng frame:
   - Chạy `model.track()` với ByteTrack
   - Filter chỉ lấy class "person" (class_id=0)
   - Lưu bbox cho mỗi track_id
4. Tính max bounding box cho mỗi track
5. Tính output_size = max_bbox * 1.2 (20% padding)
6. Save tracking data to JSON

#### Step 3: CLI Interface
```bash
python app/service/person_tracker.py yep_pickleball.mp4
```

## 4. Deliverables
- [ ] `app/service/person_tracker.py` - Main tracking script
- [ ] `app/service/tracking_output/tracking_data.json` - Output data
- [ ] Updated `pyproject.toml` với opencv-python dependency

## 5. Verification
```bash
# Run tracking
python app/service/person_tracker.py yep_pickleball.mp4

# Verify output
cat app/service/tracking_output/tracking_data.json | python -m json.tool

# Expected: JSON với tracks cho mỗi người được detect
```

## 6. Estimated Effort
- **Time:** 1-2 hours coding
- **Processing:** 5-15 minutes (CPU) / 1-3 minutes (GPU)
