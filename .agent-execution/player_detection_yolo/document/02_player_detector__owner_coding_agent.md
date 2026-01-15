# Module 02: Player Detector with Tracking

## Objective
Sử dụng YOLO để detect players và **ByteTrack** để tracking, đảm bảo mỗi player giữ nguyên ID xuyên suốt video.

## Scope

### In-scope:
- Person detection using YOLOv8
- **ByteTrack integration** cho consistent player IDs
- Filter chỉ lấy class "person"
- Bounding box + track ID extraction
- Confidence thresholding

### Out-of-scope:
- Player re-identification (khi mất track)
- Pose estimation

## Technical Approach

### 1. Model Selection
- **Model:** YOLOv8n hoặc YOLOv8s (balance speed/accuracy)
- **Framework:** ultralytics (v8.4.2)
- **Tracker:** ByteTrack (built-in với ultralytics)
- **Classes:** Chỉ detect class 0 (person)

### 2. Detection + Tracking Pipeline
```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# Sử dụng .track() thay vì .predict() để có tracking
results = model.track(
    frame, 
    classes=[0],          # Chỉ detect person
    conf=0.5,
    tracker="bytetrack.yaml",  # Sử dụng ByteTrack
    persist=True          # Giữ track ID qua các frames
)
```

### 3. Output Format
```python
@dataclass
class TrackedPlayer:
    track_id: int                    # Consistent ID across frames
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    center: tuple[int, int]
    bottom_center: tuple[int, int]   # foot position (for court mapping)
```

## Deliverables

1. **File:** `app/service/player_detector.py`
2. **Classes/Functions:**
   - `PlayerDetector` class:
     - `__init__(model_name: str = "yolov8n.pt", confidence: float = 0.5)`
     - `track(frame: np.ndarray) -> list[TrackedPlayer]`
     - `reset_tracker()` - reset track IDs khi cần

## Implementation Details

```python
from dataclasses import dataclass
from ultralytics import YOLO
import numpy as np
from typing import Optional

@dataclass
class TrackedPlayer:
    track_id: int                    # Consistent ID across frames (-1 if no track)
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    center: tuple[int, int]
    bottom_center: tuple[int, int]   # Foot position for court mapping
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


class PlayerDetector:
    PERSON_CLASS = 0
    
    def __init__(
        self, 
        model_name: str = "yolov8n.pt",
        confidence: float = 0.5,
        device: str = "auto"
    ):
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.device = device
    
    def track(self, frame: np.ndarray) -> list[TrackedPlayer]:
        """
        Detect and track players in a frame.
        Returns players with consistent track IDs across frames.
        """
        results = self.model.track(
            frame,
            classes=[self.PERSON_CLASS],
            conf=self.confidence,
            device=self.device,
            tracker="bytetrack.yaml",
            persist=True,  # CRITICAL: keeps track IDs across frames
            verbose=False
        )
        
        players = []
        for result in results:
            boxes = result.boxes
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                
                # Get track ID (may be None if tracking fails)
                track_id = int(box.id[0]) if box.id is not None else -1
                
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                bottom_center = (center_x, y2)  # Foot position
                
                players.append(TrackedPlayer(
                    track_id=track_id,
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                    center=(center_x, center_y),
                    bottom_center=bottom_center
                ))
        
        return players
    
    def reset_tracker(self):
        """Reset the tracker state (use when switching videos)."""
        self.model.predictor = None
```

## Configuration Options

```python
DETECTOR_CONFIG = {
    "model": "yolov8n.pt",  # Options: yolov8n, yolov8s, yolov8m
    "confidence": 0.5,
    "iou_threshold": 0.45,  # NMS threshold
    "max_detections": 10,   # Max players to detect
}
```

## Test Cases

```python
import cv2

# Test 1: Basic detection
detector = PlayerDetector()
frame = cv2.imread("test_frame.jpg")
players = detector.detect(frame)
assert len(players) >= 0

# Test 2: Detection format
if players:
    p = players[0]
    assert len(p.bbox) == 4
    assert 0 <= p.confidence <= 1
    assert p.bottom_center[1] == p.bbox[3]  # y2
```

## Dependencies
- ultralytics>=8.4.2
- numpy
- opencv-python

## Performance Notes
- YOLOv8n: ~5ms/frame on GPU, ~50ms on CPU
- YOLOv8s: ~8ms/frame on GPU, ~100ms on CPU
- Video 60fps → cần ~17ms/frame for realtime (nếu cần)
