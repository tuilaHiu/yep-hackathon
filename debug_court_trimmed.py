import cv2
import json
import numpy as np
from pathlib import Path

def debug_court_coordinates(video_path, coords_path, output_path):
    # Load coordinates
    with open(coords_path, 'r') as f:
        coords = json.load(f)
    
    # Get corners
    corners = coords['court_corners']
    pts = [
        corners['top_left'],
        corners['top_right'],
        corners['bottom_right'],
        corners['bottom_left']
    ]
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Failed to read video")
        return

    # Draw court
    pts_array = np.array(pts, np.int32)
    pts_array = pts_array.reshape((-1, 1, 2))
    cv2.polylines(frame, [pts_array], True, (0, 255, 0), 3)
    
    # Draw net
    if 'net' in coords:
        net = coords['net']
        cv2.line(frame, tuple(net['left']), tuple(net['right']), (0, 0, 255), 3)

    cv2.imwrite(output_path, frame)
    print(f"Debug image saved to {output_path}")

if __name__ == "__main__":
    debug_court_coordinates(
        "/home/tuilahiu/Desktop/Yep-project/video/yep_pickleball_trimmed.mp4",
        "/home/tuilahiu/Desktop/Yep-project/app/service/court_coordinates.json",
        "/home/tuilahiu/Desktop/Yep-project/court_debug_trimmed.png"
    )
