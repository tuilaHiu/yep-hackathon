# Module 01: Court Transform

## Objective
Chuyển đổi tọa độ pixel (x, y) từ video frame sang tọa độ thực trên sân pickleball (meters hoặc %).

## Scope

### In-scope:
- Perspective transform từ 4 góc sân
- Chuyển đổi pixel → court coordinates
- Hỗ trợ cả chiều thuận và nghịch

### Out-of-scope:
- Camera calibration động
- Distortion correction

## Technical Approach

### 1. Perspective Transform Matrix
Sử dụng OpenCV `cv2.getPerspectiveTransform()` với:

**Source points (pixel):** từ `court_coordinates.json`
```
top_left:     (722, 453)
top_right:    (1180, 456)
bottom_left:  (1607, 960)  
bottom_right: (317, 967)
```

**Destination points (court):** sân pickleball tiêu chuẩn
```
Kích thước: 6.1m x 13.4m (20ft x 44ft)

top_left:     (0, 0)
top_right:    (6.1, 0)
bottom_left:  (0, 13.4)
bottom_right: (6.1, 13.4)
```

### 2. Transform Function
```python
def pixel_to_court(pixel_x, pixel_y) -> tuple[float, float]:
    """Convert pixel coordinates to court coordinates in meters."""
    pass

def court_to_pixel(court_x, court_y) -> tuple[int, int]:
    """Convert court coordinates back to pixel (for visualization)."""
    pass
```

## Deliverables

1. **File:** `app/service/court_transform.py`
2. **Classes/Functions:**
   - `CourtTransform` class với methods:
     - `__init__(court_config_path: str)`
     - `pixel_to_court(x: int, y: int) -> tuple[float, float]`
     - `court_to_pixel(x: float, y: float) -> tuple[int, int]`
     - `get_court_dimensions() -> tuple[float, float]`

## Implementation Details

```python
import cv2
import numpy as np
import json
from pathlib import Path

COURT_WIDTH_M = 6.1   # 20 feet
COURT_LENGTH_M = 13.4  # 44 feet

class CourtTransform:
    def __init__(self, court_config_path: str):
        with open(court_config_path) as f:
            config = json.load(f)
        
        # Source points from video (pixel coordinates)
        corners = config["court_corners"]
        self.src_points = np.float32([
            corners["top_left"],
            corners["top_right"],
            corners["bottom_right"],
            corners["bottom_left"],
        ])
        
        # Destination points (court coordinates in meters)
        self.dst_points = np.float32([
            [0, 0],
            [COURT_WIDTH_M, 0],
            [COURT_WIDTH_M, COURT_LENGTH_M],
            [0, COURT_LENGTH_M],
        ])
        
        # Compute transform matrices
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)
        self.M_inv = cv2.getPerspectiveTransform(self.dst_points, self.src_points)
    
    def pixel_to_court(self, x: int, y: int) -> tuple[float, float]:
        point = np.float32([[x, y]]).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.M)
        return float(transformed[0][0][0]), float(transformed[0][0][1])
    
    def court_to_pixel(self, x: float, y: float) -> tuple[int, int]:
        point = np.float32([[x, y]]).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.M_inv)
        return int(transformed[0][0][0]), int(transformed[0][0][1])
```

## Test Cases

```python
# Test 1: Corner points should map correctly
transform = CourtTransform("app/service/court_coordinates.json")
assert transform.pixel_to_court(722, 453) ≈ (0, 0)
assert transform.pixel_to_court(1180, 456) ≈ (6.1, 0)

# Test 2: Round-trip conversion
px, py = 900, 600
cx, cy = transform.pixel_to_court(px, py)
px2, py2 = transform.court_to_pixel(cx, cy)
assert abs(px - px2) < 2 and abs(py - py2) < 2
```

## Dependencies
- opencv-python (cv2)
- numpy
