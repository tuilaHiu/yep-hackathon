import cv2
import json
import os
import argparse
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any, Optional

class PlayerSelector:
    """
    GUI tool for selecting players from a video frame using YOLO detections.
    """

    def __init__(self, video_path: str, frame_index: int = 0, max_players: int = 4, model_path: str = "yolov8n.pt"):
        """
        Initialize the selector.

        Args:
            video_path: Path to the video file.
            frame_index: Frame index to display for selection.
            max_players: Maximum number of players that can be selected.
            model_path: Path to the YOLO model.
        """
        self.video_path = video_path
        self.frame_index = frame_index
        self.max_players = max_players
        self.model = YOLO(model_path)
        
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame = None
        self.detections: List[Dict[str, Any]] = []
        self.selected_indices: List[int] = []
        self.player_names: Dict[int, str] = {}
        
        self.window_name = "Player Selector - Click to Select (S: Save, Q: Quit, R: Reset, N/P: Nav)"
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._on_mouse_click)
        
        self._load_frame()

    def _load_frame(self) -> None:
        """Load frame at current frame_index and run detection."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        ret, frame = self.cap.read()
        if not ret:
            print(f"Warning: Could not read frame {self.frame_index}")
            return
            
        self.frame = frame
        self._run_detection()

    def _run_detection(self) -> None:
        """Run YOLO detection on the current frame and filter for persons."""
        results = self.model(self.frame, verbose=False)
        self.detections = []
        
        # Class 0 is 'person' in COCO
        for result in results:
            boxes = result.boxes
            for box in boxes:
                if int(box.cls) == 0:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    self.detections.append({
                        "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                        "conf": float(box.conf)
                    })

    def _on_mouse_click(self, event: int, x: int, y: int, flags: int, param: Any) -> None:
        """OpenCV mouse callback."""
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, det in enumerate(self.detections):
                bbox = det["bbox"]
                if self._is_point_in_bbox(x, y, bbox):
                    self._toggle_selection(i)
                    break

    def _is_point_in_bbox(self, x: int, y: int, bbox: Dict[str, int]) -> bool:
        """Check if a point (x, y) is inside a bounding box."""
        return bbox["x1"] <= x <= bbox["x2"] and bbox["y1"] <= y <= bbox["y2"]

    def _toggle_selection(self, index: int) -> None:
        """Toggle selection state for a detection index."""
        if index in self.selected_indices:
            self.selected_indices.remove(index)
            self.player_names.pop(index, None)
        else:
            if len(self.selected_indices) >= self.max_players:
                print(f"Warning: Maximum {self.max_players} players reached.")
                return
            
            self.selected_indices.append(index)
            # Simple terminal prompt for name
            print(f"Selected Player Index {index+1}")
            name = input(f"Enter name for player {index+1} (default: Player_{index+1}): ").strip()
            if not name:
                name = f"Player_{index+1}"
            self.player_names[index] = name

    def _draw(self) -> np.ndarray:
        """Draw detections and selection state on frame."""
        display_frame = self.frame.copy()
        
        for i, det in enumerate(self.detections):
            bbox = det["bbox"]
            is_selected = i in self.selected_indices
            color = (0, 255, 0) if is_selected else (0, 0, 255)
            thickness = 3 if is_selected else 1
            
            cv2.rectangle(display_frame, (bbox["x1"], bbox["y1"]), (bbox["x2"], bbox["y2"]), color, thickness)
            
            label = f"{i+1}"
            if is_selected:
                label += f": {self.player_names.get(i, '')}"
                
            cv2.putText(display_frame, label, (bbox["x1"], bbox["y1"] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
        if not self.detections:
            cv2.putText(display_frame, "No persons detected in this frame. Press 'N'/'P' to change frame.", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
        # Info text
        info_text = f"Frame: {self.frame_index}/{self.total_frames} | Selected: {len(self.selected_indices)}/{self.max_players}"
        cv2.putText(display_frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.putText(display_frame, "S: Save | Q: Quit | R: Reset | N: Next | P: Prev", 
                    (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return display_frame

    def run(self) -> Optional[Dict[str, Any]]:
        """
        Run the GUI loop.

        Returns:
            Selected players data or None if cancelled.
        """
        while True:
            display_frame = self._draw()
            cv2.imshow(self.window_name, display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s') or key == 13: # 'S' or Enter
                return self._get_result()
            elif key == ord('q') or key == 27: # 'Q' or Esc
                return None
            elif key == ord('r'): # 'R'
                self.selected_indices = []
                self.player_names = {}
            elif key == ord('n'): # 'N'
                if self.frame_index < self.total_frames - 1:
                    self.frame_index += 1
                    self._load_frame()
            elif key == ord('p'): # 'P'
                if self.frame_index > 0:
                    self.frame_index -= 1
                    self._load_frame()
            
            # Check if window closed
            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                return None

    def _get_result(self) -> Dict[str, Any]:
        """Format the selected data into the required JSON structure."""
        players = []
        for i in self.selected_indices:
            players.append({
                "selection_id": i + 1,
                "name": self.player_names[i],
                "initial_bbox": self.detections[i]["bbox"]
            })
            
        return {
            "video_source": os.path.basename(self.video_path),
            "selection_frame": self.frame_index,
            "players": players
        }

    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()

def select_players_gui(
    video_path: str,
    frame_index: int = 0,
    max_players: int = 4,
    output_path: str | None = None
) -> Optional[Dict[str, Any]]:
    """
    Entry point for player selection GUI.
    """
    selector = PlayerSelector(video_path, frame_index, max_players)
    result = selector.run()
    
    if result and output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Selection saved to {output_path}")
        except IOError as e:
            print(f"Error saving results to {output_path}: {e}")
        
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select players to track in a video.")
    parser.add_argument("--video", type=str, required=True, help="Path to video file")
    parser.add_argument("--frame", type=int, default=0, help="Initial frame index")
    parser.add_argument("--output", type=str, default="selected_players.json", help="Output JSON path")
    parser.add_argument("--max_players", type=int, default=4, help="Max players to select")
    
    args = parser.parse_args()
    
    select_players_gui(args.video, args.frame, args.max_players, args.output)
