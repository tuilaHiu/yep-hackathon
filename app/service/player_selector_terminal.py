import cv2
import json
import os
import argparse
import numpy as np
import re
from datetime import datetime
from ultralytics import YOLO
from typing import List, Dict, Any, Optional


def save_selection_screenshot(
    frame: np.ndarray,
    players: List[Dict[str, Any]],
    output_dir: str,
    video_name: str,
    frame_index: int
) -> str:
    """
    Save a screenshot with selected players annotated.

    Args:
        frame: The video frame (numpy array).
        players: List of selected player data with 'name' and 'initial_bbox'.
        output_dir: Directory to save the screenshot.
        video_name: Name of the source video (for filename).
        frame_index: Frame index used for selection.

    Returns:
        str: Path to the saved screenshot.
    """
    annotated_frame = frame.copy()

    for p in players:
        bbox = p["initial_bbox"]
        name = p["name"]
        
        # Draw bounding box (green for selected)
        cv2.rectangle(
            annotated_frame,
            (bbox["x1"], bbox["y1"]),
            (bbox["x2"], bbox["y2"]),
            (0, 255, 0),
            3
        )
        
        # Draw name label with background
        label = f"{p['selection_id']}. {name}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Background rectangle for text
        cv2.rectangle(
            annotated_frame,
            (bbox["x1"], bbox["y1"] - text_h - 10),
            (bbox["x1"] + text_w + 5, bbox["y1"]),
            (0, 255, 0),
            -1
        )
        cv2.putText(
            annotated_frame,
            label,
            (bbox["x1"] + 2, bbox["y1"] - 5),
            font,
            font_scale,
            (0, 0, 0),
            thickness
        )

    # Add timestamp and info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"Frame: {frame_index} | Selected: {len(players)} player(s) | {timestamp}"
    cv2.putText(
        annotated_frame,
        info_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename
    base_name = os.path.splitext(video_name)[0]
    screenshot_filename = f"{base_name}_selection_frame{frame_index}.png"
    screenshot_path = os.path.join(output_dir, screenshot_filename)

    cv2.imwrite(screenshot_path, annotated_frame)
    return screenshot_path

def parse_player_input(input_str: str, max_id: int) -> List[int]:
    """
    Parse user input for player IDs.
    
    Accepts formats:
    - "1,2,3"
    - "1 2 3"
    - "1, 2, 3"
    - "1"
    
    Args:
        input_str: Raw string input from user.
        max_id: Maximum valid detection ID.
        
    Returns:
        list[int]: Valid player IDs (1-indexed).
    """
    # Find all sequences of digits
    ids = [int(x) for x in re.findall(r'\d+', input_str)]
    
    # Filter for valid IDs
    valid_ids = []
    for pid in ids:
        if 1 <= pid <= max_id:
            if pid not in valid_ids:
                valid_ids.append(pid)
        else:
            print(f"Warning: Player ID {pid} is out of range (1-{max_id}). Skipping.")
            
    return valid_ids

def select_players_terminal(
    video_path: str,
    frame_index: int = 0,
    max_players: int = 4,
    output_path: str | None = None,
    show_preview: bool = True,
    model_path: str = "yolov8n.pt"
) -> Optional[Dict[str, Any]]:
    """
    Terminal-based player selection using YOLO detection.
    
    Args:
        video_path: Path to video file
        frame_index: Frame to display for selection
        max_players: Maximum number of players to select
        output_path: Path to save selection JSON
        show_preview: Whether to show OpenCV preview window
        model_path: Path to YOLO model
    
    Returns:
        dict: Selected players data or None if cancelled
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_index >= total_frames:
        print(f"Warning: Frame index {frame_index} out of range (total {total_frames}). Setting to 0.")
        frame_index = 0

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"Error: Could not read frame {frame_index}")
        return None

    print(f"\n--- Running detection on {os.path.basename(video_path)} (Frame {frame_index}) ---")
    model = YOLO(model_path)
    results = model(frame, verbose=False)
    
    detections = []
    for result in results:
        for box in result.boxes:
            if int(box.cls) == 0:  # person
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                    "conf": float(box.conf)
                })

    if not detections:
        print("No persons detected in this frame.")
        return None

    print(f"\n=== PLAYER SELECTION ===")
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Frame: {frame_index}")
    print("\nDetected persons:")
    for i, det in enumerate(detections):
        bbox = det["bbox"]
        w = bbox["x2"] - bbox["x1"]
        h = bbox["y2"] - bbox["y1"]
        print(f"  [{i+1}] Position: ({bbox['x1']}, {bbox['y1']}) - Size: {w}x{h} - Conf: {det['conf']:.2f}")

    if show_preview:
        display_frame = frame.copy()
        for i, det in enumerate(detections):
            bbox = det["bbox"]
            cv2.rectangle(display_frame, (bbox["x1"], bbox["y1"]), (bbox["x2"], bbox["y2"]), (0, 0, 255), 2)
            cv2.putText(display_frame, f"ID: {i+1}", (bbox["x1"], bbox["y1"] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Create resizable window and fit to reasonable screen size
        window_name = "Player Selector Preview - Check Terminal"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # Calculate window size (fit to ~80% of typical screen, max 1280x720)
        frame_h, frame_w = display_frame.shape[:2]
        max_w, max_h = 1280, 720
        scale = min(max_w / frame_w, max_h / frame_h, 1.0)
        new_w, new_h = int(frame_w * scale), int(frame_h * scale)
        cv2.resizeWindow(window_name, new_w, new_h)
        
        cv2.imshow(window_name, display_frame)
        cv2.waitKey(1)  # Refresh window

    try:
        input_str = input(f"\nEnter player numbers to track (1-{len(detections)}, max {max_players}): ")
        selected_ids = parse_player_input(input_str, len(detections))
        
        if not selected_ids:
            print("No valid players selected. Exiting.")
            if show_preview: cv2.destroyAllWindows()
            return None

        if len(selected_ids) > max_players:
            print(f"Warning: Selected {len(selected_ids)} players, but max is {max_players}. Using first {max_players}.")
            selected_ids = selected_ids[:max_players]

        players = []
        for pid in selected_ids:
            name = input(f"Enter name for Player {pid} (default: Player_{pid}): ").strip()
            if not name:
                name = f"Player_{pid}"
            players.append({
                "selection_id": pid,
                "name": name,
                "initial_bbox": detections[pid - 1]["bbox"]
            })

        result = {
            "video_source": os.path.basename(video_path),
            "selection_frame": frame_index,
            "players": players
        }

        print("\n--- Selection Summary ---")
        for p in players:
            bbox = p["initial_bbox"]
            print(f"  {p['selection_id']}. {p['name']} - BBox({bbox['x1']}, {bbox['y1']}, {bbox['x2']}, {bbox['y2']})")

        confirm = input("\nConfirm selection? (y/n, default y): ").strip().lower()
        if confirm == 'n':
            print("Selection cancelled.")
            if show_preview: cv2.destroyAllWindows()
            return None

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Selection saved to: {output_path}")

        # Save selection screenshot
        output_dir = os.path.dirname(output_path) if output_path else "."
        if not output_dir:
            output_dir = "."
        screenshot_path = save_selection_screenshot(
            frame=frame,
            players=players,
            output_dir=output_dir,
            video_name=os.path.basename(video_path),
            frame_index=frame_index
        )
        print(f"Selection screenshot saved to: {screenshot_path}")
        result["screenshot_path"] = screenshot_path

        if show_preview:
            # Highlight selected players in preview before closing
            final_frame = frame.copy()
            for p in players:
                bbox = p["initial_bbox"]
                cv2.rectangle(final_frame, (bbox["x1"], bbox["y1"]), (bbox["x2"], bbox["y2"]), (0, 255, 0), 3)
                cv2.putText(final_frame, p["name"], (bbox["x1"], bbox["y1"] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Create resizable window for confirmation
            confirm_window = "Player Selector Preview - Confirmed"
            cv2.namedWindow(confirm_window, cv2.WINDOW_NORMAL)
            frame_h, frame_w = final_frame.shape[:2]
            max_w, max_h = 1280, 720
            scale = min(max_w / frame_w, max_h / frame_h, 1.0)
            new_w, new_h = int(frame_w * scale), int(frame_h * scale)
            cv2.resizeWindow(confirm_window, new_w, new_h)
            
            cv2.imshow(confirm_window, final_frame)
            print("Preview window updated. Press any key in the window or wait 2 seconds to close.")
            cv2.waitKey(2000)
            cv2.destroyAllWindows()

        return result

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        if show_preview: cv2.destroyAllWindows()
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Terminal-based player selection tool.")
    parser.add_argument("--video", type=str, required=True, help="Path to video file")
    parser.add_argument("--frame", type=int, default=0, help="Frame index to use (default: 0)")
    parser.add_argument("--output", type=str, default="selected_players.json", help="Output JSON path")
    parser.add_argument("--max_players", type=int, default=4, help="Max players to select (default: 4)")
    parser.add_argument("--no-preview", action="store_true", help="Disable OpenCV preview window")
    
    args = parser.parse_args()
    
    select_players_terminal(
        video_path=args.video,
        frame_index=args.frame,
        max_players=args.max_players,
        output_path=args.output,
        show_preview=not args.no_preview
    )
