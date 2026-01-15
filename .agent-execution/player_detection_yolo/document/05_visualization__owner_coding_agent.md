# Module 05: Visualization

## Objective
Vẽ annotations lên video frames: bounding boxes, **track IDs**, và tọa độ sân.

## Scope

### In-scope:
- Draw bounding boxes với màu theo track ID
- Display **track ID** (consistent across frames) và confidence
- Show court position (meters)
- Draw mini-map of court (optional)
- Export annotated video

### Out-of-scope:
- Real-time GUI display
- Interactive overlay

## Technical Approach

### 1. Annotation Elements

```
┌─────────────────────────────────────┐
│  Player 1 (0.95)                    │
│  Court: (2.5m, 8.3m)                │
│  ┌─────────┐                        │
│  │         │ ← Bounding Box         │
│  │   👤    │                        │
│  │         │                        │
│  └────●────┘                        │
│       ↑                             │
│  Bottom Center (foot position)      │
└─────────────────────────────────────┘
```

### 2. Color Scheme
- Player 1: Green (#00FF00)
- Player 2: Blue (#0000FF)
- Player 3: Yellow (#FFFF00)
- Player 4: Red (#FF0000)
- Bounding box: 2px solid
- Text: White with black outline

## Deliverables

1. **File:** `app/service/visualization.py`
2. **Classes/Functions:**
   - `Visualizer` class:
     - `draw_player(frame, player_data, color)`
     - `draw_court_overlay(frame, court_transform)`
     - `draw_minimap(frame, players, court_dims)`
     - `create_annotated_video(video_path, results, output_path)`

## Implementation Details

```python
import cv2
import numpy as np
from typing import Optional
from pathlib import Path

# Color palette for players (BGR format)
PLAYER_COLORS = [
    (0, 255, 0),    # Green
    (255, 0, 0),    # Blue
    (0, 255, 255),  # Yellow
    (0, 0, 255),    # Red
]


class Visualizer:
    def __init__(
        self,
        font_scale: float = 0.6,
        line_thickness: int = 2,
        show_confidence: bool = True,
        show_court_position: bool = True
    ):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = font_scale
        self.line_thickness = line_thickness
        self.show_confidence = show_confidence
        self.show_court_position = show_court_position
    
    def draw_player(
        self,
        frame: np.ndarray,
        player_data: dict,
        player_id: int = 0
    ) -> np.ndarray:
        """Draw bounding box and info for a player."""
        color = PLAYER_COLORS[player_id % len(PLAYER_COLORS)]
        
        # Extract data
        x1, y1, x2, y2 = player_data["bbox"]
        conf = player_data["confidence"]
        court_pos = player_data.get("court_position", [0, 0])
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, self.line_thickness)
        
        # Draw bottom center point (foot position)
        px, py = player_data["pixel_position"]
        cv2.circle(frame, (px, py), 5, color, -1)
        
        # Prepare label text
        label_parts = [f"P{player_id + 1}"]
        if self.show_confidence:
            label_parts.append(f"{conf:.0%}")
        label = " ".join(label_parts)
        
        # Draw label background
        (label_w, label_h), _ = cv2.getTextSize(
            label, self.font, self.font_scale, self.line_thickness
        )
        cv2.rectangle(
            frame,
            (x1, y1 - label_h - 10),
            (x1 + label_w + 5, y1),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            frame, label,
            (x1 + 2, y1 - 5),
            self.font, self.font_scale,
            (0, 0, 0), self.line_thickness
        )
        
        # Draw court position below box
        if self.show_court_position:
            court_label = f"({court_pos[0]:.1f}m, {court_pos[1]:.1f}m)"
            cv2.putText(
                frame, court_label,
                (x1, y2 + 20),
                self.font, self.font_scale * 0.8,
                color, 1
            )
        
        return frame
    
    def draw_court_lines(
        self,
        frame: np.ndarray,
        court_corners: dict,
        net_points: Optional[dict] = None
    ) -> np.ndarray:
        """Draw court boundary lines on frame."""
        # Court corners
        corners = [
            tuple(court_corners["top_left"]),
            tuple(court_corners["top_right"]),
            tuple(court_corners["bottom_right"]),
            tuple(court_corners["bottom_left"]),
        ]
        
        # Draw court boundary
        for i in range(4):
            cv2.line(
                frame,
                corners[i],
                corners[(i + 1) % 4],
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
        
        # Draw net
        if net_points:
            cv2.line(
                frame,
                tuple(net_points["left"]),
                tuple(net_points["right"]),
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )
        
        return frame
    
    def draw_minimap(
        self,
        frame: np.ndarray,
        players: list[dict],
        court_dims: tuple[float, float] = (6.1, 13.4),
        position: tuple[int, int] = (20, 20),
        size: tuple[int, int] = (100, 220)
    ) -> np.ndarray:
        """Draw a minimap showing player positions on court."""
        map_w, map_h = size
        court_w, court_l = court_dims
        
        # Create minimap background
        minimap = np.zeros((map_h, map_w, 3), dtype=np.uint8)
        minimap[:] = (50, 50, 50)  # Dark gray background
        
        # Draw court outline
        cv2.rectangle(minimap, (2, 2), (map_w - 2, map_h - 2), (200, 200, 200), 1)
        
        # Draw center line (net)
        net_y = map_h // 2
        cv2.line(minimap, (0, net_y), (map_w, net_y), (255, 255, 255), 1)
        
        # Draw players
        for i, player in enumerate(players):
            court_x, court_y = player.get("court_position", [0, 0])
            
            # Convert court coords to minimap coords
            mx = int((court_x / court_w) * map_w)
            my = int((court_y / court_l) * map_h)
            
            # Clamp to minimap bounds
            mx = max(5, min(map_w - 5, mx))
            my = max(5, min(map_h - 5, my))
            
            color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            cv2.circle(minimap, (mx, my), 5, color, -1)
        
        # Overlay minimap on frame
        x, y = position
        frame[y:y+map_h, x:x+map_w] = minimap
        
        return frame
    
    def annotate_frame(
        self,
        frame: np.ndarray,
        frame_data: dict,
        court_config: Optional[dict] = None
    ) -> np.ndarray:
        """Apply all annotations to a frame."""
        annotated = frame.copy()
        
        # Draw court lines
        if court_config:
            annotated = self.draw_court_lines(
                annotated,
                court_config.get("court_corners", {}),
                court_config.get("net")
            )
        
        # Draw players
        players = frame_data.get("players", [])
        for player in players:
            pid = player.get("player_id", 0)
            annotated = self.draw_player(annotated, player, pid)
        
        # Draw minimap
        if players:
            annotated = self.draw_minimap(annotated, players)
        
        # Draw frame info
        frame_id = frame_data.get("frame_id", 0)
        timestamp = frame_data.get("timestamp_sec", 0)
        info_text = f"Frame: {frame_id} | Time: {timestamp:.2f}s"
        cv2.putText(
            annotated, info_text,
            (frame.shape[1] - 300, 30),
            self.font, 0.6, (255, 255, 255), 1
        )
        
        return annotated
    
    def create_annotated_video(
        self,
        input_video: str,
        results: dict,
        output_path: str,
        court_config: Optional[dict] = None
    ) -> str:
        """Create annotated video from results."""
        cap = cv2.VideoCapture(input_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create frame lookup
        frame_results = {f["frame_id"]: f for f in results.get("frames", [])}
        
        frame_id = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_id in frame_results:
                frame = self.annotate_frame(
                    frame,
                    frame_results[frame_id],
                    court_config
                )
            
            out.write(frame)
            frame_id += 1
        
        cap.release()
        out.release()
        
        return output_path
```

## Usage Example

```python
from visualization import Visualizer
import json

# Load results
with open("output/player_tracking.json") as f:
    results = json.load(f)

with open("app/service/court_coordinates.json") as f:
    court_config = json.load(f)

# Create annotated video
viz = Visualizer()
viz.create_annotated_video(
    input_video="video/yep_pickleball.mp4",
    results=results,
    output_path="output/annotated_video.mp4",
    court_config=court_config
)
```

## Dependencies
- opencv-python
- numpy
