# Module 03: Court Filter

## Objective
Filter các detections để **chỉ giữ lại players có vị trí trong sân**, loại bỏ khán giả, trọng tài và những người ngoài sân.

## Scope

### In-scope:
- Kiểm tra player có trong court polygon không
- Sử dụng foot position (bottom_center) để xác định vị trí
- Buffer zone cho edge cases
- Logging khi detect > 4 players (cảnh báo)

### Out-of-scope:
- Role classification (player vs referee)
- Team assignment

## Technical Approach

### 1. Court Polygon Definition
Sử dụng 4 góc sân từ `court_coordinates.json` để tạo polygon:

```
           top_left ─────────── top_right
              │                     │
              │       COURT         │
              │                     │
         bottom_left ───────── bottom_right
```

### 2. Point-in-Polygon Check
- Sử dụng **foot position** (bottom_center) của player
- Áp dụng buffer zone để tránh filter nhầm players sát biên

### 3. Filter Logic
```python
def is_inside_court(foot_position, court_polygon, buffer_px=20):
    """Check if player's foot is inside court (+buffer)."""
    x, y = foot_position
    # Expand polygon by buffer
    # Check point in polygon
    return cv2.pointPolygonTest(court_polygon, (x, y), False) >= 0
```

## Deliverables

1. **File:** `app/service/court_filter.py`
2. **Classes/Functions:**
   - `CourtFilter` class:
     - `__init__(court_config_path: str, buffer_px: int = 20)`
     - `filter_players(players: list[TrackedPlayer]) -> list[TrackedPlayer]`
     - `is_inside_court(x: int, y: int) -> bool`

## Implementation Details

```python
import cv2
import numpy as np
import json
from dataclasses import dataclass
from typing import Optional

from .player_detector import TrackedPlayer


class CourtFilter:
    """Filter detections to only keep players inside the court."""
    
    MAX_PLAYERS_ON_COURT = 4  # Doubles match
    
    def __init__(
        self,
        court_config_path: str,
        buffer_px: int = 20  # Buffer zone around court boundary
    ):
        with open(court_config_path) as f:
            config = json.load(f)
        
        # Build court polygon from corners
        corners = config["court_corners"]
        self.court_polygon = np.array([
            corners["top_left"],
            corners["top_right"],
            corners["bottom_right"],
            corners["bottom_left"],
        ], dtype=np.float32)
        
        self.buffer_px = buffer_px
        
        # Create expanded polygon for buffer zone
        self.expanded_polygon = self._expand_polygon(
            self.court_polygon, 
            buffer_px
        )
    
    def _expand_polygon(
        self, 
        polygon: np.ndarray, 
        buffer: int
    ) -> np.ndarray:
        """
        Expand polygon outward by buffer pixels.
        Simple approach: move each point away from center.
        """
        center = polygon.mean(axis=0)
        expanded = []
        
        for point in polygon:
            direction = point - center
            direction_norm = direction / (np.linalg.norm(direction) + 1e-6)
            new_point = point + direction_norm * buffer
            expanded.append(new_point)
        
        return np.array(expanded, dtype=np.float32)
    
    def is_inside_court(self, x: int, y: int) -> bool:
        """
        Check if a point is inside the court (with buffer).
        Uses foot position of player.
        """
        point = (float(x), float(y))
        
        # Check against expanded polygon (court + buffer)
        result = cv2.pointPolygonTest(
            self.expanded_polygon.reshape(-1, 1, 2),
            point,
            measureDist=False
        )
        
        return result >= 0  # 1 = inside, 0 = on edge, -1 = outside
    
    def filter_players(
        self, 
        players: list[TrackedPlayer],
        log_warnings: bool = True
    ) -> list[TrackedPlayer]:
        """
        Filter players to only keep those inside the court.
        
        Args:
            players: List of detected/tracked players
            log_warnings: If True, log warning when > 4 players detected
            
        Returns:
            Filtered list of players inside court
        """
        filtered = []
        
        for player in players:
            foot_x, foot_y = player.bottom_center
            
            if self.is_inside_court(foot_x, foot_y):
                filtered.append(player)
        
        # Warn if too many players detected (possible false positives)
        if log_warnings and len(filtered) > self.MAX_PLAYERS_ON_COURT:
            import logging
            logging.warning(
                f"Detected {len(filtered)} players inside court "
                f"(expected max {self.MAX_PLAYERS_ON_COURT})"
            )
        
        return filtered
    
    def get_court_polygon(self) -> np.ndarray:
        """Get the court polygon for visualization."""
        return self.court_polygon.copy()
    
    def get_expanded_polygon(self) -> np.ndarray:
        """Get the expanded court polygon (with buffer)."""
        return self.expanded_polygon.copy()
```

## Usage Example

```python
from player_detector import PlayerDetector, TrackedPlayer
from court_filter import CourtFilter

# Initialize
detector = PlayerDetector()
court_filter = CourtFilter(
    court_config_path="app/service/court_coordinates.json",
    buffer_px=20
)

# Process frame
players = detector.track(frame)
print(f"Detected: {len(players)} players")

# Filter to court only
court_players = court_filter.filter_players(players)
print(f"In court: {len(court_players)} players")
```

## Test Cases

```python
# Test 1: Point inside court
filter = CourtFilter("app/service/court_coordinates.json")
assert filter.is_inside_court(950, 700) == True  # Center of court

# Test 2: Point outside court (spectator area)
assert filter.is_inside_court(100, 100) == False  # Top-left corner of video

# Test 3: Point on edge (with buffer)
# Should be included due to buffer zone
edge_point = (722, 453)  # Exactly on top-left corner
assert filter.is_inside_court(*edge_point) == True

# Test 4: Filter function
from player_detector import TrackedPlayer

players = [
    TrackedPlayer(1, (100, 200, 150, 300), 0.9, (125, 250), (125, 300)),  # Outside
    TrackedPlayer(2, (800, 500, 900, 700), 0.95, (850, 600), (850, 700)),  # Inside
]
filtered = filter.filter_players(players)
assert len(filtered) == 1
assert filtered[0].track_id == 2
```

## Configuration

```python
FILTER_CONFIG = {
    "buffer_px": 20,        # Pixels of buffer around court
    "max_players": 4,       # Max expected players (for warnings)
    "log_warnings": True,   # Log when > max_players detected
}
```

## Dependencies
- opencv-python (cv2)
- numpy
- Module: player_detector (for TrackedPlayer dataclass)
