"""
Tool to extract court coordinates from a pickleball video frame.

Instructions:
1. Run this script with your video path
2. Click on the points in this order:
   - 4 corners of the court (top-left, top-right, bottom-right, bottom-left)
   - 2 points of the net (left end, right end)
3. Press 'S' to save coordinates
4. Press 'R' to reset and start over
5. Press 'Q' to quit
"""

import cv2
import json
import argparse
from pathlib import Path

# Store clicked points
points = []
point_labels = [
    "Court Top-Left",
    "Court Top-Right", 
    "Court Bottom-Right",
    "Court Bottom-Left",
    "Net Left",
    "Net Right",
    # Additional court lines (optional)
    "Kitchen Line Near-Left",
    "Kitchen Line Near-Right",
    "Kitchen Line Far-Left",
    "Kitchen Line Far-Right",
]

current_frame = None
display_frame = None


def mouse_callback(event, x, y, flags, param):
    """Handle mouse click events."""
    global points, display_frame
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < len(point_labels):
            points.append((x, y))
            print(f"Point {len(points)}: {point_labels[len(points)-1]} = ({x}, {y})")
            update_display()
        else:
            print("All points collected! Press 'S' to save or 'R' to reset.")


def update_display():
    """Update the display with current points."""
    global display_frame, current_frame, points
    
    display_frame = current_frame.copy()
    
    # Draw points
    colors = [
        (0, 255, 0),    # Green - Court corners
        (0, 255, 0),
        (0, 255, 0),
        (0, 255, 0),
        (0, 0, 255),    # Red - Net
        (0, 0, 255),
        (255, 255, 0),  # Cyan - Kitchen lines
        (255, 255, 0),
        (255, 255, 0),
        (255, 255, 0),
    ]
    
    for i, point in enumerate(points):
        color = colors[i] if i < len(colors) else (255, 255, 255)
        cv2.circle(display_frame, point, 5, color, -1)
        cv2.circle(display_frame, point, 8, color, 2)
        
        # Add label
        label = f"{i+1}: {point_labels[i]}"
        cv2.putText(display_frame, label, (point[0] + 10, point[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Draw lines connecting court corners
    if len(points) >= 4:
        for i in range(4):
            cv2.line(display_frame, points[i], points[(i+1) % 4], (0, 255, 0), 2)
    
    # Draw net line
    if len(points) >= 6:
        cv2.line(display_frame, points[4], points[5], (0, 0, 255), 2)
    
    # Draw kitchen lines
    if len(points) >= 8:
        cv2.line(display_frame, points[6], points[7], (255, 255, 0), 2)
    if len(points) >= 10:
        cv2.line(display_frame, points[8], points[9], (255, 255, 0), 2)
    
    # Show instructions
    instructions = [
        f"Click to mark: {point_labels[len(points)]} ({len(points)+1}/{len(point_labels)})" if len(points) < len(point_labels) else "All points marked!",
        "S: Save | R: Reset | Q: Quit | Z: Undo last point"
    ]
    
    for i, text in enumerate(instructions):
        cv2.putText(display_frame, text, (10, 30 + i * 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow("Court Coordinate Extractor", display_frame)


def save_coordinates(output_path: str):
    """Save coordinates to a JSON file."""
    global points
    
    if len(points) < 6:
        print("Need at least 6 points (4 corners + 2 net points) to save!")
        return False
    
    coords = {
        "court_corners": {
            "top_left": points[0],
            "top_right": points[1],
            "bottom_right": points[2],
            "bottom_left": points[3],
        },
        "net": {
            "left": points[4],
            "right": points[5],
        },
    }
    
    # Add kitchen lines if available
    if len(points) >= 8:
        coords["kitchen_line_near"] = {
            "left": points[6],
            "right": points[7],
        }
    if len(points) >= 10:
        coords["kitchen_line_far"] = {
            "left": points[8],
            "right": points[9],
        }
    
    # Also save as flat list for easy access
    coords["all_points"] = {
        point_labels[i]: points[i] for i in range(len(points))
    }
    
    with open(output_path, 'w') as f:
        json.dump(coords, f, indent=2)
    
    print(f"\n✅ Coordinates saved to: {output_path}")
    print("\n📋 Court Coordinates:")
    print(json.dumps(coords, indent=2))
    
    return True


def extract_frame(video_path: str, frame_number: int = 0):
    """Extract a frame from the video."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Video: {video_path}")
    print(f"Total frames: {total_frames}, FPS: {fps:.2f}")
    
    # Seek to frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    
    if not ret:
        raise ValueError(f"Cannot read frame {frame_number}")
    
    cap.release()
    return frame


def main():
    global current_frame, display_frame, points
    
    parser = argparse.ArgumentParser(description="Extract court coordinates from video")
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--frame", type=int, default=100, help="Frame number to extract (default: 100)")
    parser.add_argument("--output", default="court_coordinates.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Check if video exists
    if not Path(args.video_path).exists():
        print(f"❌ Video not found: {args.video_path}")
        return
    
    print("\n🏸 Pickleball Court Coordinate Extractor")
    print("=" * 50)
    
    # Extract frame
    current_frame = extract_frame(args.video_path, args.frame)
    update_display()
    
    # Set up mouse callback
    cv2.setMouseCallback("Court Coordinate Extractor", mouse_callback)
    
    print("\n📍 Click points in this order:")
    for i, label in enumerate(point_labels):
        print(f"   {i+1}. {label}")
    print("\n⌨️  Keyboard shortcuts:")
    print("   S - Save coordinates")
    print("   R - Reset all points")
    print("   Z - Undo last point")
    print("   Q - Quit")
    print("   +/- - Navigate frames")
    
    frame_offset = 0
    cap = cv2.VideoCapture(args.video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            save_coordinates(args.output)
        elif key == ord('r'):
            points = []
            print("\n🔄 Reset - all points cleared")
            update_display()
        elif key == ord('z'):
            if points:
                removed = points.pop()
                print(f"↩️  Undo: removed point at {removed}")
                update_display()
        elif key == ord('+') or key == ord('='):
            frame_offset = min(frame_offset + 30, total_frames - args.frame - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, args.frame + frame_offset)
            ret, current_frame = cap.read()
            if ret:
                print(f"Frame: {args.frame + frame_offset}")
                update_display()
        elif key == ord('-'):
            frame_offset = max(frame_offset - 30, -args.frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, args.frame + frame_offset)
            ret, current_frame = cap.read()
            if ret:
                print(f"Frame: {args.frame + frame_offset}")
                update_display()
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
