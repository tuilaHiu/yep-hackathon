# Project Context Documentation

## 1. Project Overview
- **Purpose:** Pickleball tracking and analysis system using computer vision.
- **Primary users:** Pickleball players, coaches, analysts.
- **Main features:**
  - Player detection and tracking.
  - Court boundary detection and coordinate mapping.
  - Perspective transformation (pixel frame to court meters).
  - Visualization of tracking data on video.

## 2. Tech Stack
- **Language:** Python >= 3.12
- **Key libraries:**
  - `opencv-python`: Image processing and perspective transformation.
  - `ultralytics`: YOLO model for object detection.
  - `numpy`: Numerical operations.
  - `tqdm`: Progress bars.

## 3. Directory Structure
```
yep-project/
├── .agent/
├── .agent-execution/
│   └── player_detection_yolo/
├── .venv/
├── app/
│   └── service/
│       ├── court_coordinates.json
│       └── extract_court_coordinates.py
├── video/
│   └── yep_pickleball.mp4
├── main.py
├── pyproject.toml
└── uv.lock
```

- **app/service/:** Contains core service logic and configuration.
  - `court_coordinates.json`: Stores calibrated court corner points.
  - `extract_court_coordinates.py`: Utility to manually extract court points from video frames.
- **video/:** Stores input video files.
- **.agent-execution/:** Stores agent plans and logs.

## 4. Architecture & Data Flow
- **Architecture:** Modular script-based processing pipeline.
- **Data Flow:**
  1. **Input:** Raw video (`.mp4`) + Court Configuration (`.json`).
  2. **Preprocessing:** Frame extraction.
  3. **Detection:** YOLO model identifies players (bounding boxes).
  4. **Tracking:** ByteTrack assigns persistent IDs to players across frames.
  5. **Filtering:** Filter out detections outside the court boundaries.
  6. **Transformation:** Convert bounding box positions (foot) to real-world court coordinates (meters) using Perspective Transform.
  7. **Output:** JSON file with tracking data + Annotated Video.

## 5. How to Run & Test
- **Setup Environment:**
  ```bash
  uv venv
  source .venv/bin/activate
  uv pip sync  # or install dependencies manually
  ```
- **Helper Tool:**
  - Run court extractor: `python app/service/extract_court_coordinates.py video/yep_pickleball.mp4`
- **Main Pipeline (Proposed):**
  - Run processor: `python app/service/video_processor.py` (To be implemented)

## 6. Recent Changes (Auto)
- Project initialized.
- `extract_court_coordinates.py` created and operational.
- Planning documents for `player_detection_yolo` created.
