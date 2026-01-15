# Module 04: Video Processor

## Objective
Pipeline chính để xử lý video: đọc frames → detect + track players → filter court → transform coordinates → output results.

## Scope

### In-scope:
- Video reading/writing
- **Process ALL frames** (3709 frames, không skip)
- Player tracking integration (ByteTrack)
- Court filtering integration
- Coordinate transformation
- JSON output generation
- Progress tracking

### Out-of-scope:
- Realtime streaming
- Multi-video batch processing

## Technical Approach

### 1. Processing Pipeline
```
Video Input (3709 frames @ 60fps)
    ↓
Frame Extraction (EVERY frame)
    ↓
Player Detection + Tracking (Module 02) → Consistent track IDs
    ↓
Court Filtering (Module 03) → Remove spectators/referees
    ↓
Coordinate Transform (Module 01) → Pixel to court meters
    ↓
Results Aggregation
    ↓
JSON Output + Annotated Video
```

### 2. Output Format

**JSON Structure:**
```json
{
  "video_info": {
    "path": "video/yep_pickleball.mp4",
    "fps": 60,
    "total_frames": 3709,
    "resolution": [1920, 1080],
    "duration_sec": 61.82
  },
  "court_dimensions": {
    "width_m": 6.1,
    "length_m": 13.4
  },
  "processing_config": {
    "model": "yolov8n.pt",
    "confidence": 0.5,
    "tracker": "bytetrack",
    "court_filter_buffer_px": 20
  },
  "frames": [
    {
      "frame_id": 0,
      "timestamp_sec": 0.0,
      "players": [
        {
          "track_id": 1,
          "bbox": [100, 200, 150, 350],
          "confidence": 0.92,
          "pixel_position": [125, 350],
          "court_position": [2.5, 8.3]
        }
      ]
    }
  ],
  "summary": {
    "frames_processed": 3709,
    "unique_tracks": 4,
    "avg_players_per_frame": 3.8
  }
}
```

## Deliverables

1. **File:** `app/service/video_processor.py`
2. **Classes/Functions:**
   - `VideoProcessor` class:
     - `__init__(video_path, court_config, output_dir)`
     - `process()` - process ALL frames (no skip parameter)
     - `save_results(output_path)`
     - `get_summary()`

## Implementation Details

```python
import cv2
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from tqdm import tqdm
from typing import Optional
import logging

from .player_detector import PlayerDetector, TrackedPlayer
from .court_transform import CourtTransform
from .court_filter import CourtFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    frame_id: int
    timestamp_sec: float
    players: list[dict]


class VideoProcessor:
    """
    Main pipeline for processing pickleball video.
    Processes ALL frames with tracking and court filtering.
    """
    
    def __init__(
        self,
        video_path: str,
        court_config_path: str,
        output_dir: str = "output",
        model_name: str = "yolov8n.pt",
        confidence: float = 0.5,
        court_filter_buffer_px: int = 20
    ):
        self.video_path = video_path
        self.court_config_path = court_config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store config for output
        self.config = {
            "model": model_name,
            "confidence": confidence,
            "tracker": "bytetrack",
            "court_filter_buffer_px": court_filter_buffer_px
        }
        
        # Initialize components
        self.detector = PlayerDetector(model_name, confidence)
        self.transform = CourtTransform(court_config_path)
        self.court_filter = CourtFilter(court_config_path, court_filter_buffer_px)
        
        # Video info
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_sec = self.total_frames / self.fps
        
        self.results: list[FrameResult] = []
        self.unique_track_ids: set[int] = set()
        
        logger.info(f"Video loaded: {self.total_frames} frames @ {self.fps:.0f}fps ({self.duration_sec:.1f}s)")
    
    def process(self, show_progress: bool = True) -> list[FrameResult]:
        """
        Process ALL frames in the video.
        No skip_frames parameter - we process every frame.
        """
        self.detector.reset_tracker()  # Ensure clean tracking state
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        frame_range = range(self.total_frames)
        if show_progress:
            frame_range = tqdm(frame_range, desc="Processing frames", unit="frame")
        
        for frame_id in frame_range:
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning(f"Failed to read frame {frame_id}")
                break
            
            # Step 1: Detect + Track players
            all_players = self.detector.track(frame)
            
            # Step 2: Filter to court only (remove spectators/referees)
            court_players = self.court_filter.filter_players(all_players)
            
            # Step 3: Transform coordinates and build output
            player_data = []
            for player in court_players:
                # Track unique IDs
                if player.track_id >= 0:
                    self.unique_track_ids.add(player.track_id)
                
                # Transform foot position to court coordinates
                court_x, court_y = self.transform.pixel_to_court(
                    player.bottom_center[0],
                    player.bottom_center[1]
                )
                
                player_data.append({
                    "track_id": player.track_id,
                    "bbox": list(player.bbox),
                    "confidence": round(player.confidence, 3),
                    "pixel_position": list(player.bottom_center),
                    "court_position": [round(court_x, 2), round(court_y, 2)]
                })
            
            self.results.append(FrameResult(
                frame_id=frame_id,
                timestamp_sec=round(frame_id / self.fps, 3),
                players=player_data
            ))
        
        logger.info(f"Processing complete: {len(self.results)} frames, {len(self.unique_track_ids)} unique tracks")
        return self.results
    
    def save_results(self, output_path: Optional[str] = None) -> str:
        """Save results to JSON file."""
        if output_path is None:
            output_path = self.output_dir / "player_tracking.json"
        
        output = {
            "video_info": {
                "path": str(self.video_path),
                "fps": self.fps,
                "total_frames": self.total_frames,
                "resolution": [self.width, self.height],
                "duration_sec": round(self.duration_sec, 2)
            },
            "court_dimensions": {
                "width_m": 6.1,
                "length_m": 13.4
            },
            "processing_config": self.config,
            "frames": [asdict(r) for r in self.results],
            "summary": self.get_summary()
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return str(output_path)
    
    def get_summary(self) -> dict:
        """Get processing summary."""
        total_detections = sum(len(r.players) for r in self.results)
        avg_players = total_detections / len(self.results) if self.results else 0
        
        return {
            "frames_processed": len(self.results),
            "unique_tracks": len(self.unique_track_ids),
            "total_detections": total_detections,
            "avg_players_per_frame": round(avg_players, 2)
        }
    
    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()
```

## Usage Example

```python
processor = VideoProcessor(
    video_path="video/yep_pickleball.mp4",
    court_config_path="app/service/court_coordinates.json",
    output_dir="output"
)

# Process ALL frames (no skip_frames option anymore)
results = processor.process()

# Save results
output_path = processor.save_results()
print(f"Results saved to: {output_path}")

# Print summary
print(processor.get_summary())
# Output: {'frames_processed': 3709, 'unique_tracks': 4, 'total_detections': 14836, 'avg_players_per_frame': 4.0}
```

## Performance Notes

- **3709 frames @ 60fps** = ~62 seconds of video
- Estimated processing time:
  - GPU (RTX 3060+): ~3-5 minutes
  - CPU only: ~30-60 minutes
- Memory: ~2-4GB RAM for video buffer

## Dependencies
- opencv-python
- tqdm (progress bar)
- Modules: player_detector, court_transform, court_filter

