"""
Named Video Cropper module - Extract videos for named players.

This module specialized in cropping video for specific players identified by name.
It supports adding black frames for missing tracking periods and sanitizing player names
to safe filenames.
"""

import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
from tqdm import tqdm

from app.service.video_cropper import (
    FOURCC,
    convert_to_h264,
    create_black_frame,
    crop_and_pad_frame,
    load_tracking_data,
)


def sanitize_filename(name: str) -> str:
    """
    Convert player name to a safe filename.

    Removes diacritics, converts to lowercase, replaces non-alphanumeric
    characters with underscores, and strips multiple underscores.

    Args:
        name: The player name to sanitize.

    Returns:
        str: A safe, sanitized filename.

    Examples:
        "Nguyen Van A" -> "nguyen_van_a"
        "Player #1" -> "player_1"
        "Trần" -> "tran"
        "!!!" -> "player_unknown"
    """
    if not name or not any(c.isalnum() for c in name):
        return "player_unknown"

    # Normalize unicode characters to remove diacritics (e.g., Trần -> Tran)
    name = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )

    # Convert to lowercase
    name = name.lower()

    # Replace any non-alphanumeric character with underscore
    name = re.sub(r"[^a-z0-9]+", "_", name)

    # Strip leading/trailing underscores
    name = name.strip("_")

    if not name:
        return "player_unknown"

    return name


def crop_named_player_videos(
    video_path: str,
    tracking_data_path: str,
    output_dir: str | None = None,
    include_black_frames: bool = True,
) -> list[str]:
    """
    Crop video for each named player in the tracking data.

    Args:
        video_path: Path to source video.
        tracking_data_path: Path to selective_tracking_data.json.
        output_dir: Directory where output videos will be saved.
        include_black_frames: If True, include black frames when player is missing.

    Returns:
        list[str]: Paths to generated video files.

    Raises:
        FileNotFoundError: If video or tracking data file does not exist.
        RuntimeError: If video cannot be opened.
        ValueError: If tracking data is empty.
    """
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Load selective tracking data
    tracking_data = load_tracking_data(tracking_data_path)
    if not tracking_data.get("tracks") and not tracking_data.get("selected_players"):
        raise ValueError("Tracking data is empty. No persons to extract.")

    # Setup output directory
    if output_dir is None:
        output_dir_obj = Path(__file__).parent / "named_output_videos"
    else:
        output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

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

    # Process names and handle duplicates
    if "tracks" in tracking_data:
        tracks = tracking_data["tracks"]
        raw_names = [data.get("name", f"player_{tid}") for tid, data in tracks.items()]
    elif "selected_players" in tracking_data:
        # Convert selected_players list to tracks-like dict for internal processing
        tracks = {
            str(i): player for i, player in enumerate(tracking_data["selected_players"])
        }
        raw_names = [player.get("name", f"player_{i}") for i, player in tracks.items()]
    else:
        raise ValueError("Tracking data must contain 'tracks' or 'selected_players' key.")

    sanitized_names = [sanitize_filename(name) for name in raw_names]
    
    # Handle duplicates by adding suffixes
    final_filenames: list[str] = []
    counts = Counter()
    for name in sanitized_names:
        if name in sanitized_names:
            if sanitized_names.count(name) > 1:
                counts[name] += 1
                final_filenames.append(f"{name}_{counts[name]}")
            else:
                final_filenames.append(name)
        else:
            final_filenames.append(name)

    # Prepare output video writers
    output_files: list[str] = []
    writers: dict[str, cv2.VideoWriter] = {}
    track_id_to_filename: dict[str, str] = {}
    
    for (track_id, track_data), filename in zip(tracks.items(), final_filenames):
        output_size = track_data["output_size"]
        output_file = output_dir_obj / f"{filename}.mp4"
        output_files.append(str(output_file))

        writer = cv2.VideoWriter(
            str(output_file),
            FOURCC,
            fps,
            (output_size["width"], output_size["height"]),
        )
        writers[track_id] = writer
        track_id_to_filename[track_id] = filename

    print(f"\nStarting video cropping for {len(writers)} persons...")

    # Process each frame
    frame_idx = 0
    pbar = tqdm(total=total_frames, desc="Cropping videos")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_str = str(frame_idx)

            for track_id, writer in writers.items():
                track_data = tracks[track_id]
                output_size = track_data["output_size"]

                if frame_str in track_data["frames"]:
                    bbox = track_data["frames"][frame_str]
                    cropped = crop_and_pad_frame(frame, bbox, output_size)
                    writer.write(cropped)
                elif include_black_frames:
                    # Check if the track has started or if we should always write black frames
                    # Usually we want the output video to be the same duration as the source segment
                    # if it's "selective tracking", it might start mid-segment.
                    # But the requirement says "Frame đen khi người không xuất hiện".
                    # Let's write black frames for the entire duration to keep timing synced with original.
                    black_frame = create_black_frame(output_size)
                    writer.write(black_frame)

            frame_idx += 1
            pbar.update(1)
            
            # Optional: break if we reached total_frames from info (safety)
            if frame_idx >= total_frames:
                break

    finally:
        pbar.close()
        cap.release()
        for writer in writers.values():
            writer.release()

    print(f"\nCropping complete. Processed {frame_idx} frames.")
    print(f"Output videos saved to: {output_dir_obj}")

    # Convert videos to H.264 for web/VSCode compatibility
    print("\nConverting videos to H.264 format...")
    for video_file in output_files:
        if convert_to_h264(video_file):
            print(f"  ✓ Converted: {video_file}")
        else:
            print(f"  ✗ Failed to convert: {video_file}")

    return output_files


def main() -> None:
    """
    CLI entry point for named video cropping.
    """
    parser = argparse.ArgumentParser(
        description="Crop video to extract individual named player videos"
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
        help="Path to selective tracking JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory to save output videos",
    )
    parser.add_argument(
        "--no-black-frames",
        action="store_false",
        dest="include_black_frames",
        help="Do not include black frames for missing tracking data",
    )
    parser.set_defaults(include_black_frames=True)

    args = parser.parse_args()

    try:
        output_files = crop_named_player_videos(
            args.video,
            args.tracking,
            args.output,
            args.include_black_frames,
        )
        print("\nGenerated files:")
        for f in output_files:
            print(f"  - {f}")
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
