import cv2
import json
import argparse
from pathlib import Path
import numpy as np

def crop_video_to_court(video_path, coords_path, output_path, padding=50):
    """
    Crops the video to the bounding box of the court coordinates.
    """
    # Load coordinates
    if not Path(coords_path).exists():
        print(f"Error: Coordinates file not found: {coords_path}")
        return

    with open(coords_path, 'r') as f:
        coords = json.load(f)
    
    # Get all points to find the overall bounding box
    points = []
    if 'court_corners' in coords:
        points.extend(coords['court_corners'].values())
    if 'net' in coords:
        points.extend(coords['net'].values())
    
    if not points:
        print("Error: No coordinates found in JSON")
        return

    pts = np.array(points)
    x_min, y_min = np.min(pts, axis=0)
    x_max, y_max = np.max(pts, axis=0)

    # Add padding
    x_min = max(0, int(x_min - padding))
    y_min = max(0, int(y_min - padding))
    
    # We need to get original video dimensions for capping max values
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    x_max = min(frame_width, int(x_max + padding))
    y_max = min(frame_height, int(y_max + padding))

    # Calculate final dimensions (ensure they are even for some codecs)
    out_width = (x_max - x_min) // 2 * 2
    out_height = (y_max - y_min) // 2 * 2
    
    print(f"Original size: {frame_width}x{frame_height}")
    print(f"Crop box: x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]")
    print(f"Output size: {out_width}x{out_height}")

    # Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (out_width, out_height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Crop frame
        cropped_frame = frame[y_min:y_min+out_height, x_min:x_min+out_width]
        out.write(cropped_frame)
        
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processing frame {frame_count}/{total_frames}...", end='\r')

    cap.release()
    out.release()
    print(f"\nFinished! Saved cropped video to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop video to court areas")
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--coords", type=str, default="app/service/court_coordinates.json", help="Path to court coordinates JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output video")
    parser.add_argument("--padding", type=int, default=50, help="Padding around the court bounding box")
    
    args = parser.parse_args()
    
    crop_video_to_court(args.video, args.coords, args.output, args.padding)
