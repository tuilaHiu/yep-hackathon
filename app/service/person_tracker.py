"""
Person detection and tracking module using YOLO + ByteTrack.

This module processes video files to detect and track all persons present,
using YOLOv8 for detection and ByteTrack for multi-object tracking.
The output is a JSON file containing tracking data for each detected person.
"""
import argparse
import json
import math
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


# Constants
PERSON_CLASS_ID = 0  # COCO class ID for "person"
PADDING_FACTOR = 1.2  # 20% padding for output size
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "tracking_output"


def calculate_max_bbox(frames_data: dict[str, dict[str, int]]) -> dict[str, int]:
    """
    Calculate the maximum bounding box dimensions across all frames for a track.

    Args:
        frames_data: Dictionary mapping frame numbers to bbox coordinates.
            Each bbox has keys: x1, y1, x2, y2.

    Returns:
        dict: Maximum width and height observed across all frames.
    """
    max_width = 0
    max_height = 0

    for bbox in frames_data.values():
        width = bbox["x2"] - bbox["x1"]
        height = bbox["y2"] - bbox["y1"]
        max_width = max(max_width, width)
        max_height = max(max_height, height)

    return {"width": max_width, "height": max_height}


def calculate_output_size(max_bbox: dict[str, int]) -> dict[str, int]:
    """
    Calculate output video size with padding applied.

    Args:
        max_bbox: Dictionary with "width" and "height" of max bounding box.

    Returns:
        dict: Output width and height with padding applied, rounded up to even numbers.
    """
    # Apply padding factor
    padded_width = int(math.ceil(max_bbox["width"] * PADDING_FACTOR))
    padded_height = int(math.ceil(max_bbox["height"] * PADDING_FACTOR))

    # Ensure even dimensions for video encoding compatibility
    if padded_width % 2 != 0:
        padded_width += 1
    if padded_height % 2 != 0:
        padded_height += 1

    return {"width": padded_width, "height": padded_height}


def run_tracking(video_path: str, output_dir: str | None = None) -> dict[str, Any]:
    """
    Run YOLO detection with ByteTrack on video.

    This function processes a video file frame by frame, using YOLOv8 to detect
    persons and ByteTrack to maintain consistent track IDs across frames.

    Args:
        video_path: Path to input video file.
        output_dir: Directory to save tracking data. Defaults to tracking_output/.

    Returns:
        dict: Tracking data with video info and all tracks.

    Raises:
        FileNotFoundError: If video file does not exist.
        RuntimeError: If video cannot be opened.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Set up output directory
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video info: {width}x{height}, {fps} FPS, {total_frames} frames")

    # Initialize YOLO model
    model = YOLO("yolov8n.pt")  # Using nano model for speed

    # Tracking data structure
    tracking_data: dict[str, Any] = {
        "video_info": {
            "source": video_path.name,
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
        },
        "tracks": {},
    }

    frame_idx = 0
    print("Starting tracking...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLO tracking with ByteTrack
        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=[PERSON_CLASS_ID],  # Only detect persons
            verbose=False,
        )

        # Process detections
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes
            for i, box in enumerate(boxes):
                # Get track ID
                if boxes.id is None:
                    continue
                track_id = str(int(boxes.id[i].item()))

                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                }

                # Initialize track if new
                if track_id not in tracking_data["tracks"]:
                    tracking_data["tracks"][track_id] = {"frames": {}}

                # Store frame data
                tracking_data["tracks"][track_id]["frames"][str(frame_idx)] = bbox

        # Progress update
        if frame_idx % 100 == 0:
            print(f"Processed frame {frame_idx}/{total_frames}")

        frame_idx += 1

    cap.release()
    print(f"Tracking complete. Processed {frame_idx} frames.")

    # Calculate max bbox and output size for each track
    for track_id, track_data in tracking_data["tracks"].items():
        max_bbox = calculate_max_bbox(track_data["frames"])
        output_size = calculate_output_size(max_bbox)
        track_data["max_bbox"] = max_bbox
        track_data["output_size"] = output_size

    # Summary
    num_tracks = len(tracking_data["tracks"])
    print(f"Found {num_tracks} unique person tracks.")

    # Save tracking data
    output_file = output_dir / "tracking_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tracking_data, f, indent=2)

    print(f"Tracking data saved to: {output_file}")

    return tracking_data


def main() -> None:
    """
    CLI entry point for person tracking.

    Usage:
        python app/service/person_tracker.py <video_path> [--output-dir <dir>]
    """
    parser = argparse.ArgumentParser(
        description="Detect and track persons in video using YOLO + ByteTrack"
    )
    parser.add_argument(
        "video_path",
        type=str,
        help="Path to input video file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save tracking data (default: app/service/tracking_output/)",
    )

    args = parser.parse_args()

    run_tracking(args.video_path, args.output_dir)


if __name__ == "__main__":
    main()
