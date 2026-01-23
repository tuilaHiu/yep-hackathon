"""
Video cropping module - Extract individual person videos.

This module reads tracking data from the person_tracker module and crops
the original video to extract separate videos for each tracked person.
Each output video has a fixed size based on the maximum bounding box
observed for that person (plus 20% padding).
"""
import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


# Constants
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output_videos"
FOURCC = cv2.VideoWriter_fourcc(*"mp4v")  # MP4 codec (will be converted to H.264)


def convert_to_h264(input_path: str) -> bool:
    """
    Convert video to H.264 codec using ffmpeg for web/VSCode compatibility.
    
    Args:
        input_path: Path to the input video file.
        
    Returns:
        bool: True if conversion successful, False otherwise.
    """
    import subprocess
    import shutil
    
    input_file = Path(input_path)
    temp_file = input_file.with_suffix(".temp.mp4")
    
    try:
        # Run ffmpeg to convert to H.264
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(input_file),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-movflags", "+faststart",  # Enable fast start for web playback
                str(temp_file)
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Replace original with converted file
            shutil.move(str(temp_file), str(input_file))
            return True
        else:
            print(f"FFmpeg conversion failed: {result.stderr}")
            if temp_file.exists():
                temp_file.unlink()
            return False
    except FileNotFoundError:
        print("Warning: ffmpeg not found. Video will remain in mp4v format.")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False


def load_tracking_data(tracking_data_path: str) -> dict[str, Any]:
    """
    Load tracking data from JSON file.

    Args:
        tracking_data_path: Path to the tracking JSON file from module 01.

    Returns:
        dict: Tracking data containing video_info and tracks.

    Raises:
        FileNotFoundError: If tracking data file does not exist.
        json.JSONDecodeError: If JSON file is malformed.
    """
    path = Path(tracking_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Tracking data file not found: {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def crop_and_pad_frame(
    frame: np.ndarray,
    bbox: dict[str, int],
    output_size: dict[str, int],
) -> np.ndarray:
    """
    Crop a region from frame and pad to output size.

    The cropped region is centered within the output frame with black padding.
    If the bbox extends beyond frame boundaries, those areas are filled black.

    Args:
        frame: Source video frame (BGR format).
        bbox: Bounding box with keys x1, y1, x2, y2.
        output_size: Target output size with keys width, height.

    Returns:
        np.ndarray: Cropped and padded frame of size (output_height, output_width, 3).
    """
    frame_h, frame_w = frame.shape[:2]
    out_w = output_size["width"]
    out_h = output_size["height"]

    # Get bbox coordinates (ensure they are integers)
    x1, y1 = int(bbox["x1"]), int(bbox["y1"])
    x2, y2 = int(bbox["x2"]), int(bbox["y2"])
    bbox_w = x2 - x1
    bbox_h = y2 - y1

    # Calculate center of bbox
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    # Calculate crop region (centered around bbox center, size = output_size)
    crop_x1 = center_x - out_w // 2
    crop_y1 = center_y - out_h // 2
    crop_x2 = crop_x1 + out_w
    crop_y2 = crop_y1 + out_h

    # Create output frame (black background)
    output_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)

    # Calculate valid regions (handle edge cases where crop extends beyond frame)
    src_x1 = max(0, crop_x1)
    src_y1 = max(0, crop_y1)
    src_x2 = min(frame_w, crop_x2)
    src_y2 = min(frame_h, crop_y2)

    # Calculate destination region in output frame
    dst_x1 = src_x1 - crop_x1
    dst_y1 = src_y1 - crop_y1
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    # Ensure all indices are integers before slicing
    indices = [src_x1, src_y1, src_x2, src_y2, dst_x1, dst_y1, dst_x2, dst_y2]
    src_y1, src_y2, src_x1, src_x2, dst_y1, dst_y2, dst_x1, dst_x2 = map(int, [src_y1, src_y2, src_x1, src_x2, dst_y1, dst_y2, dst_x1, dst_x2])

    # Only copy if there's a valid region
    if src_x2 > src_x1 and src_y2 > src_y1:
        output_frame[dst_y1:dst_y2, dst_x1:dst_x2] = frame[src_y1:src_y2, src_x1:src_x2]

    return output_frame


def create_black_frame(output_size: dict[str, int]) -> np.ndarray:
    """
    Create a black frame of the specified size.

    Args:
        output_size: Target output size with keys width, height.

    Returns:
        np.ndarray: Black frame of size (height, width, 3).
    """
    return np.zeros((output_size["height"], output_size["width"], 3), dtype=np.uint8)


def crop_person_videos(
    video_path: str,
    tracking_data_path: str,
    output_dir: str | None = None,
    min_frames: int = 0,
) -> list[str]:
    """
    Crop video to extract individual person videos.

    For each tracked person, this function creates a separate video file
    containing only that person, cropped from the original video with
    consistent framing based on their maximum bounding box.

    Args:
        video_path: Path to original video file.
        tracking_data_path: Path to tracking JSON from module 01.
        output_dir: Directory to save output videos. Defaults to output_videos/.
        min_frames: Minimum number of frames a track must appear in to be
            included. Tracks with fewer frames are skipped. Default 0 (no filter).

    Returns:
        list[str]: Paths to generated video files.

    Raises:
        FileNotFoundError: If video or tracking data file does not exist.
        RuntimeError: If video cannot be opened.
        ValueError: If tracking data is empty or no tracks pass filter.
    """
    # Validate inputs
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Load tracking data
    tracking_data = load_tracking_data(tracking_data_path)

    # Check for empty tracking data
    if not tracking_data.get("tracks"):
        raise ValueError("Tracking data is empty. No persons to extract.")

    # Filter tracks by minimum frame count
    all_tracks = tracking_data["tracks"]
    if min_frames > 0:
        filtered_tracks = {
            tid: data for tid, data in all_tracks.items()
            if len(data["frames"]) >= min_frames
        }
        print(f"Filtering: keeping tracks with >= {min_frames} frames")
        print(f"  Original tracks: {len(all_tracks)}")
        print(f"  After filter: {len(filtered_tracks)}")
    else:
        filtered_tracks = all_tracks

    if not filtered_tracks:
        raise ValueError(
            f"No tracks pass the min_frames filter ({min_frames}). "
            f"Try lowering the threshold."
        )

    # Setup output directory
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open source video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    # Get video properties
    video_info = tracking_data["video_info"]
    fps = video_info["fps"]
    total_frames = video_info["total_frames"]

    print(f"Source video: {video_info['source']}")
    print(f"Video properties: {video_info['width']}x{video_info['height']}, {fps} FPS")
    print(f"Total frames: {total_frames}")
    print(f"Number of persons to extract: {len(filtered_tracks)}")

    # Prepare output video writers for each track
    output_files: list[str] = []
    writers: dict[str, cv2.VideoWriter] = {}
    track_data_map: dict[str, dict[str, Any]] = {}

    for track_id, track_data in filtered_tracks.items():
        output_size = track_data["output_size"]
        output_file = output_dir / f"person_{track_id}.mp4"
        output_files.append(str(output_file))

        writer = cv2.VideoWriter(
            str(output_file),
            FOURCC,
            fps,
            (output_size["width"], output_size["height"]),
        )
        writers[track_id] = writer
        track_data_map[track_id] = track_data

    print(f"\nStarting video cropping for {len(writers)} persons...")

    # Process each frame
    frame_idx = 0
    frames_written: dict[str, int] = {tid: 0 for tid in writers}

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_str = str(frame_idx)

        # Write cropped frame for each track (only when person is present)
        for track_id, writer in writers.items():
            track_data = track_data_map[track_id]

            if frame_str in track_data["frames"]:
                # Person is in this frame - crop and pad
                output_size = track_data["output_size"]
                bbox = track_data["frames"][frame_str]
                cropped = crop_and_pad_frame(frame, bbox, output_size)
                writer.write(cropped)
                frames_written[track_id] += 1

        # Progress update
        if frame_idx % 500 == 0:
            print(f"Processed frame {frame_idx}/{total_frames}")

        frame_idx += 1

    # Cleanup
    cap.release()
    for writer in writers.values():
        writer.release()

    print(f"\nCropping complete. Processed {frame_idx} frames.")
    print(f"Output videos saved to: {output_dir}")
    print(f"Generated {len(output_files)} video files.")

    return output_files


def main() -> None:
    """
    CLI entry point for video cropping.

    Usage:
        python app/service/video_cropper.py \\
            --video <video_path> \\
            --tracking <tracking_json_path> \\
            [--output <output_dir>]
    """
    parser = argparse.ArgumentParser(
        description="Crop video to extract individual person videos"
    )
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to input video file",
    )
    parser.add_argument(
        "--tracking",
        type=str,
        required=True,
        help="Path to tracking JSON from module 01",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory to save output videos (default: app/service/output_videos/)",
    )
    parser.add_argument(
        "--min-frames",
        type=int,
        default=0,
        help="Minimum number of frames a track must appear in (default: 0 = no filter)",
    )

    args = parser.parse_args()

    try:
        output_files = crop_person_videos(
            args.video, args.tracking, args.output, args.min_frames
        )
        print("\nGenerated files:")
        for f in output_files[:10]:  # Show first 10
            print(f"  - {f}")
        if len(output_files) > 10:
            print(f"  ... and {len(output_files) - 10} more")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise SystemExit(1) from e
    except ValueError as e:
        print(f"Warning: {e}")
        raise SystemExit(0) from e
    except RuntimeError as e:
        print(f"Error: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
