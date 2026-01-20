import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

from app.service.color_histogram import (
    compare_histograms,
    extract_color_histogram,
    update_histogram_ema,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_iou(box1: Dict[str, float], box2: Dict[str, float]) -> float:
    """
    Calculate Intersection over Union (IOU) between two bounding boxes.

    Args:
        box1: Bounding box with keys x1, y1, x2, y2.
        box2: Bounding box with keys x1, y1, x2, y2.

    Returns:
        float: IOU value between 0 and 1.
    """
    x1 = max(box1["x1"], box2["x1"])
    y1 = max(box1["y1"], box2["y1"])
    x2 = min(box1["x2"], box2["x2"])
    y2 = min(box1["y2"], box2["y2"])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
    area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def match_bbox_to_detections(
    target_bbox: Dict[str, float],
    detections: List[Dict[str, Any]],
    iou_threshold: float = 0.3,
) -> Optional[int]:
    """
    Find best matching detection for target bbox.

    Args:
        target_bbox: Bounding box to match.
        detections: List of detection dicts (must contain 'bbox' as [x1, y1, x2, y2]).
        iou_threshold: Minimum IOU for a match.

    Returns:
        Optional[int]: Index of best match in detections, or None if no good match.
    """
    best_iou = 0.0
    best_idx = None

    for i, det in enumerate(detections):
        det_bbox = {
            "x1": det["bbox"][0],
            "y1": det["bbox"][1],
            "x2": det["bbox"][2],
            "y2": det["bbox"][3],
        }
        iou = calculate_iou(target_bbox, det_bbox)
        if iou > best_iou and iou >= iou_threshold:
            best_iou = iou
            best_idx = i
    
    return best_idx


def hybrid_rematch(
    frame: np.ndarray,
    last_bbox: Dict[str, float],
    reference_histogram: np.ndarray,
    frames_lost: int,
    current_detections: List[Dict[str, Any]],
    assigned_track_ids: Set[int],
    base_speed: float = 5.0,
    max_distance_cap: float = 500.0,
    similarity_threshold: float = 0.5,
    distance_weight: float = 0.3,
    histogram_weight: float = 0.7,
) -> Tuple[Optional[int], Optional[Dict[str, float]], Optional[np.ndarray]]:
    """
    Hybrid re-identification using spatial distance + color histogram.

    Algorithm:
    1. Calculate max allowed distance based on frames_lost
    2. Filter candidates by center distance
    3. For each candidate, extract histogram and compare
    4. Score = distance_weight * distance_score + histogram_weight * histogram_score
    5. Return best match above threshold

    Args:
        frame: Current video frame (BGR).
        last_bbox: Last known bounding box of the player.
        reference_histogram: Reference color histogram of the player.
        frames_lost: Number of frames since track was lost.
        current_detections: List of current YOLO detections.
        assigned_track_ids: Set of track IDs already assigned to other players.
        base_speed: Estimated player speed in pixels per frame.
        max_distance_cap: Maximum search radius in pixels.
        similarity_threshold: Minimum combined score for a valid match.
        distance_weight: Weight for distance score (0-1).
        histogram_weight: Weight for histogram score (0-1).

    Returns:
        Tuple of:
            - track_id: New track ID if match found, else None
            - bbox: New bounding box if match found, else None
            - histogram: New histogram if match found (for EMA update), else None
    """
    # Step 1: Calculate max allowed distance
    max_distance = min(base_speed * frames_lost, max_distance_cap)

    # Calculate last center
    last_cx = (last_bbox["x1"] + last_bbox["x2"]) / 2
    last_cy = (last_bbox["y1"] + last_bbox["y2"]) / 2

    best_score = 0
    best_match = (None, None, None)

    for det in current_detections:
        track_id = det.get("track_id")
        if track_id is None or track_id in assigned_track_ids:
            continue

        det_bbox = {
            "x1": det["bbox"][0],
            "y1": det["bbox"][1],
            "x2": det["bbox"][2],
            "y2": det["bbox"][3],
        }

        # Step 2: Calculate center distance
        det_cx = (det_bbox["x1"] + det_bbox["x2"]) / 2
        det_cy = (det_bbox["y1"] + det_bbox["y2"]) / 2
        distance = ((det_cx - last_cx)**2 + (det_cy - last_cy)**2)**0.5

        # Skip if too far
        if distance > max_distance:
            continue

        # Step 3: Extract histogram and compare
        det_histogram = extract_color_histogram(frame, det_bbox)
        if det_histogram is None:
            continue
            
        histogram_similarity = compare_histograms(reference_histogram, det_histogram)

        # Normalize histogram similarity to 0-1 range (CORREL returns -1 to 1)
        histogram_score = (histogram_similarity + 1) / 2

        # Distance score (1 = close, 0 = far)
        distance_score = 1 - (distance / max_distance) if max_distance > 0 else 1.0

        # Step 4: Combined score
        combined_score = (
            distance_weight * distance_score +
            histogram_weight * histogram_score
        )

        if combined_score > best_score and combined_score >= similarity_threshold:
            best_score = combined_score
            best_match = (track_id, det_bbox, det_histogram)

    if best_match[0] is not None:
        logger.info(
            f"Re-matched player: track_id={best_match[0]}, "
            f"score={best_score:.2f}, "
            f"max_dist={max_distance:.1f}px"
        )
    
    return best_match


def run_selective_tracking(
    video_path: str,
    selected_players_path: str,
    output_path: Optional[str] = None,
    iou_threshold: float = 0.5,
    model_path: str = "yolo11n.pt",
    max_frames: Optional[int] = None,
    # New hybrid tracking parameters
    base_speed: float = 5.0,
    max_distance_cap: float = 500.0,
    similarity_threshold: float = 0.4,
    histogram_ema_alpha: float = 0.1,
    # Fixed output size (width, height) - if provided, overrides auto-calculated size
    fixed_output_size: Optional[Tuple[int, int]] = None,
) -> Dict[str, Any]:
    """
    Track only selected players throughout the video.

    Args:
        video_path: Path to the input video.
        selected_players_path: Path to the JSON file with selected players.
        output_path: Path to save the tracking data.
        iou_threshold: Minimum IOU for re-matching.
        model_path: Path to the YOLO model.
        max_frames: Maximum frames to process.
        base_speed: Estimated player measurement speed (pixels/frame).
        max_distance_cap: Maximum search radius for re-matching (pixels).
        similarity_threshold: Minimum score for hybrid matching.
        histogram_ema_alpha: EMA weight for histogram update.

    Returns:
        Dict[str, Any]: Tracking data.
    """
    import json
    import os
    # Load selected players
    with open(selected_players_path, "r") as f:
        selection_data = json.load(f)
    
    selected_players = selection_data.get("players", [])
    selection_frame_idx = selection_data.get("selection_frame", 0)
    
    # Initialize trackers and data structures
    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    tracking_results = {
        "video_info": {
            "source": os.path.basename(video_path),
            "fps": fps,
            "total_frames": total_frames,
            "width": width,
            "height": height,
        },
        "selected_players": []
    }
    
    # Player tracking state
    player_states = []
    for p in selected_players:
        player_states.append({
            "name": p["name"],
            "selection_id": p["selection_id"],
            "current_track_id": None,
            "last_bbox": p["initial_bbox"],
            "reference_histogram": None,  # Will be initialized on first frame
            "frames_lost": 0,             # Counter for lost frames
            "frames": {},
            "max_bbox": {"width": 0, "height": 0},
            "missing_frames": []
        })

    frame_idx = 0
    pbar = tqdm(total=total_frames, desc="Tracking players")
    
    while cap.isOpened():
        if max_frames is not None and frame_idx >= max_frames:
            break
            
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run YOLO track
        results = model.track(frame, persist=True, verbose=False)
        
        detections = []
        if results and results[0].boxes:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().tolist()
                track_id = int(boxes.id[i].cpu().item()) if boxes.id is not None else None
                detections.append({
                    "bbox": bbox,
                    "track_id": track_id
                })
        
        assigned_track_ids = set()
        
        # === PASS 1: Update players with active track IDs ===
        for state in player_states:
            if state["current_track_id"] is not None:
                found = False
                for det in detections:
                    if det["track_id"] == state["current_track_id"]:
                        bbox_dict = {
                            "x1": int(det["bbox"][0]),
                            "y1": int(det["bbox"][1]),
                            "x2": int(det["bbox"][2]),
                            "y2": int(det["bbox"][3]),
                        }
                        state["frames"][str(frame_idx)] = bbox_dict
                        state["last_bbox"] = bbox_dict
                        state["frames_lost"] = 0  # Reset counter
                        assigned_track_ids.add(state["current_track_id"])
                        
                        # Update reference histogram with EMA
                        if state["reference_histogram"] is not None:
                            new_hist = extract_color_histogram(frame, bbox_dict)
                            if new_hist is not None:
                                state["reference_histogram"] = update_histogram_ema(
                                    state["reference_histogram"], 
                                    new_hist, 
                                    alpha=histogram_ema_alpha
                                )
                        
                        # Update max bbox
                        w = bbox_dict["x2"] - bbox_dict["x1"]
                        h = bbox_dict["y2"] - bbox_dict["y1"]
                        state["max_bbox"]["width"] = max(state["max_bbox"]["width"], w)
                        state["max_bbox"]["height"] = max(state["max_bbox"]["height"], h)
                        found = True
                        break
                
                if not found:
                    state["current_track_id"] = None
                    state["frames_lost"] += 1

        # === PASS 2: Initialize or Re-match lost players ===
        for state in player_states:
            if state["current_track_id"] is None:
                # Initialize histogram on first detection
                if state["reference_histogram"] is None:
                    # First time - match by IOU only
                    match_idx = match_bbox_to_detections(
                        state["last_bbox"], 
                        detections, 
                        iou_threshold=0.3
                    )
                    if match_idx is not None:
                        det = detections[match_idx]
                        det_bbox = {
                            "x1": int(det["bbox"][0]),
                            "y1": int(det["bbox"][1]),
                            "x2": int(det["bbox"][2]),
                            "y2": int(det["bbox"][3]),
                        }
                        state["current_track_id"] = det["track_id"]
                        state["last_bbox"] = det_bbox
                        state["frames"][str(frame_idx)] = det_bbox
                        state["frames_lost"] = 0
                        assigned_track_ids.add(det["track_id"])
                        
                        # Extract initial histogram
                        state["reference_histogram"] = extract_color_histogram(
                            frame, det_bbox
                        )
                        
                        # Update max bbox
                        w = det_bbox["x2"] - det_bbox["x1"]
                        h = det_bbox["y2"] - det_bbox["y1"]
                        state["max_bbox"]["width"] = max(state["max_bbox"]["width"], w)
                        state["max_bbox"]["height"] = max(state["max_bbox"]["height"], h)
                else:
                    # Re-match using hybrid approach
                    new_id, new_bbox, new_hist = hybrid_rematch(
                        frame=frame,
                        last_bbox=state["last_bbox"],
                        reference_histogram=state["reference_histogram"],
                        frames_lost=state["frames_lost"],
                        current_detections=detections,
                        assigned_track_ids=assigned_track_ids,
                        base_speed=base_speed,
                        max_distance_cap=max_distance_cap,
                        similarity_threshold=similarity_threshold,
                    )
                    
                    if new_id is not None:
                        state["current_track_id"] = new_id
                        state["last_bbox"] = new_bbox
                        state["frames"][str(frame_idx)] = new_bbox
                        state["frames_lost"] = 0
                        assigned_track_ids.add(new_id)
                        
                        # Update histogram with EMA (slightly higher alpha after re-match)
                        state["reference_histogram"] = update_histogram_ema(
                            state["reference_histogram"],
                            new_hist,
                            alpha=min(1.0, histogram_ema_alpha * 1.5)
                        )
                        
                        # Update max bbox
                        w = new_bbox["x2"] - new_bbox["x1"]
                        h = new_bbox["y2"] - new_bbox["y1"]
                        state["max_bbox"]["width"] = max(state["max_bbox"]["width"], w)
                        state["max_bbox"]["height"] = max(state["max_bbox"]["height"], h)
                    elif frame_idx >= selection_frame_idx:
                        state["frames_lost"] += 1
                        state["missing_frames"].append(frame_idx)

        frame_idx += 1
        pbar.update(1)
        
    cap.release()
    pbar.close()
    
    # Post-process: calculate output_size and compile results
    for state in player_states:
        # Use fixed size if provided, otherwise max_bbox + 20% padding
        if fixed_output_size is not None:
            state["output_size"] = {
                "width": fixed_output_size[0],
                "height": fixed_output_size[1]
            }
        else:
            state["output_size"] = {
                "width": int(state["max_bbox"]["width"] * 1.2),
                "height": int(state["max_bbox"]["height"] * 1.2)
            }
        
        tracking_results["selected_players"].append({
            "name": state["name"],
            "selection_id": state["selection_id"],
            "frames": state["frames"],
            "max_bbox": {
                "width": int(state["max_bbox"]["width"]),
                "height": int(state["max_bbox"]["height"])
            },
            "output_size": state["output_size"],
            "frame_count": len(state["frames"]),
            "missing_frames": state["missing_frames"]
        })
        
    if output_path:
        with open(output_path, "w") as f:
            json.dump(tracking_results, f, indent=2)
            
    return tracking_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Selective Player Tracking")
    parser.add_argument("--video", type=str, required=True, help="Path to video file")
    parser.add_argument("--selected", type=str, required=True, help="Path to selected_players.json")
    parser.add_argument("--output", type=str, default="selective_tracking_data.json", help="Path to output JSON")
    parser.add_argument("--iou-threshold", type=float, default=0.5, help="IOU threshold for matching")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--max-frames", type=int, default=None, help="Maximum frames to process")
    
    # New hybrid tracking arguments
    parser.add_argument("--base-speed", type=float, default=5.0,
                        help="Player movement speed estimate (pixels/frame)")
    parser.add_argument("--max-distance", type=float, default=500.0,
                        help="Maximum search radius for re-matching (pixels)")
    parser.add_argument("--similarity-threshold", type=float, default=0.4,
                        help="Minimum score for hybrid matching")
    parser.add_argument("--histogram-alpha", type=float, default=0.1,
                        help="EMA weight for histogram update")
    
    args = parser.parse_args()
    
    run_selective_tracking(
        video_path=args.video,
        selected_players_path=args.selected,
        output_path=args.output,
        iou_threshold=args.iou_threshold,
        model_path=args.model,
        max_frames=args.max_frames,
        base_speed=args.base_speed,
        max_distance_cap=args.max_distance,
        similarity_threshold=args.similarity_threshold,
        histogram_ema_alpha=args.histogram_alpha
    )
