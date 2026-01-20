"""
Main Integration & CLI for Interactive Player Tracking.
This script coordinates player selection, tracking, and video cropping phases.
"""
import argparse
import json
import os
import sys
from typing import List, Optional, Tuple

# Add project root to sys.path to support direct execution
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.service.named_video_cropper import crop_named_player_videos
from app.service.player_selector_gui import select_players_gui
from app.service.player_selector_terminal import select_players_terminal
from app.service.selective_tracker import run_selective_tracking


def run_interactive_tracking(
    video_path: str,
    mode: str = "terminal",
    output_dir: str = "output",
    selected_players_path: Optional[str] = None,
    tracking_data_path: Optional[str] = None,
    include_black_frames: bool = True,
    max_players: int = 4,
    frame_index: int = 0,
    model_path: str = "yolo11n.pt",
    iou_threshold: float = 0.5,
    # New hybrid tracking parameters
    base_speed: float = 5.0,
    max_distance_cap: float = 500.0,
    similarity_threshold: float = 0.4,
    histogram_ema_alpha: float = 0.1,
    # Fixed output size
    fixed_output_size: Optional[Tuple[int, int]] = None,
) -> List[str]:
    """
    Run the full interactive player tracking pipeline.

    Args:
        video_path: Path to input video file.
        mode: Selection mode ("gui" or "terminal").
        output_dir: Directory to save all outputs.
        selected_players_path: Optional path to pre-existing selection JSON.
        tracking_data_path: Optional path to pre-existing tracking JSON.
        include_black_frames: Whether to include black frames for missing detections.
        max_players: Maximum number of players to select.
        frame_index: Frame index to use for selection.
        model_path: Path to the YOLO model.
        iou_threshold: IOU threshold for tracking re-match.

    Returns:
        List[str]: Paths to the generated player video files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # --- Step 1: Player Selection ---
    if tracking_data_path:
        print(f"Skipping selection and tracking, using existing tracking data: {tracking_data_path}")
        final_tracking_path = tracking_data_path
    elif selected_players_path:
        print(f"Skipping selection, using existing selection data: {selected_players_path}")
        final_selection_path = selected_players_path
    else:
        print(f"\n--- Phase 1: Player Selection ({mode} mode) ---")
        final_selection_path = os.path.join(output_dir, "selected_players.json")
        
        if mode.lower() == "gui":
            selection_result = select_players_gui(
                video_path=video_path,
                frame_index=frame_index,
                max_players=max_players,
                output_path=final_selection_path
            )
        else:
            selection_result = select_players_terminal(
                video_path=video_path,
                frame_index=frame_index,
                max_players=max_players,
                output_path=final_selection_path
            )
            
        if not selection_result:
            print("Player selection cancelled or failed. Exiting.")
            return []
        
        print(f"Selection saved to: {final_selection_path}")

    # --- Step 2: Selective Tracking ---
    if tracking_data_path:
        final_tracking_path = tracking_data_path
    else:
        print("\n--- Phase 2: Selective Tracking ---")
        final_tracking_path = os.path.join(output_dir, "selective_tracking_data.json")
        
        run_selective_tracking(
            video_path=video_path,
            selected_players_path=final_selection_path,
            output_path=final_tracking_path,
            iou_threshold=iou_threshold,
            model_path=model_path,
            base_speed=base_speed,
            max_distance_cap=max_distance_cap,
            similarity_threshold=similarity_threshold,
            histogram_ema_alpha=histogram_ema_alpha,
            fixed_output_size=fixed_output_size
        )
        print(f"Tracking data saved to: {final_tracking_path}")

    # --- Step 3: Video Cropping ---
    print("\n--- Phase 3: Video Cropping ---")
    video_paths = crop_named_player_videos(
        video_path=video_path,
        tracking_data_path=final_tracking_path,
        output_dir=output_dir,
        include_black_frames=include_black_frames
    )
    
    print(f"\nSuccessfully generated {len(video_paths)} videos:")
    for p in video_paths:
        print(f"  - {p}")
        
    return video_paths


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Interactive Player Tracking & Extraction Pipeline")
    
    # Required arguments
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    
    # Pipeline control
    parser.add_argument("--mode", type=str, choices=["gui", "terminal"], default="terminal", 
                        help="Selection mode: 'gui' or 'terminal' (default: terminal)")
    parser.add_argument("--output-dir", type=str, default="output", 
                        help="Directory for all outputs (default: output)")
    
    # Resuming
    parser.add_argument("--selected", type=str, help="Skip selection, use existing selection JSON")
    parser.add_argument("--tracking", type=str, help="Skip selection and tracking, use existing tracking JSON")
    
    # Configuration
    parser.add_argument("--max-players", type=int, default=4, help="Max players to select (default: 4)")
    parser.add_argument("--no-black-frames", action="store_false", dest="black_frames", 
                        help="Skip black frames for missing detections")
    parser.add_argument("--frame", type=int, default=0, help="Frame index for selection (default: 0)")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="YOLO model path")
    parser.add_argument("--iou", type=float, default=0.5, help="IOU threshold for tracking (default: 0.5)")
    
    # New hybrid tracking arguments
    parser.add_argument("--base-speed", type=float, default=5.0,
                        help="Player movement speed estimate (pixels/frame)")
    parser.add_argument("--max-distance", type=float, default=500.0,
                        help="Maximum search radius for re-matching (pixels)")
    parser.add_argument("--similarity-threshold", type=float, default=0.4,
                        help="Minimum score for hybrid matching")
    parser.add_argument("--histogram-alpha", type=float, default=0.1,
                        help="EMA weight for histogram update")
    parser.add_argument("--fixed-size", type=str, default=None,
                        help="Fixed output video size WxH (e.g., 200x500). Overrides auto-calculated size.")

    args = parser.parse_args()
    
    # Parse fixed size if provided
    fixed_output_size = None
    if args.fixed_size:
        try:
            w, h = args.fixed_size.lower().split('x')
            fixed_output_size = (int(w), int(h))
            print(f"Using fixed output size: {fixed_output_size[0]}x{fixed_output_size[1]}")
        except ValueError:
            print(f"Error: Invalid fixed-size format '{args.fixed_size}'. Use WxH format (e.g., 200x500)")
            sys.exit(1)

    try:
        run_interactive_tracking(
            video_path=args.video,
            mode=args.mode,
            output_dir=args.output_dir,
            selected_players_path=args.selected,
            tracking_data_path=args.tracking,
            include_black_frames=args.black_frames,
            max_players=args.max_players,
            frame_index=args.frame,
            model_path=args.model,
            iou_threshold=args.iou,
            base_speed=args.base_speed,
            max_distance_cap=args.max_distance,
            similarity_threshold=args.similarity_threshold,
            histogram_ema_alpha=args.histogram_alpha,
            fixed_output_size=fixed_output_size
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user. Progress saved in output directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
