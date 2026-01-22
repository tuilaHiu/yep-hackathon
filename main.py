import os
import sys
import json
import argparse
from typing import List

# Setup project path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.service.track_player import run_interactive_tracking
from pickleball_advice.main import analyze_pickleball_video

def main():
    parser = argparse.ArgumentParser(description="Full Pipeline: Tracking -> Analysis")
    parser.add_argument("--video", type=str, default="pickleball.mp4", help="Input video file")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    args = parser.parse_args()

    video_path = args.video
    output_dir = args.output_dir

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return

    # --- Phase 1 & 2 & 3: Tracking & Cropping ---
    # We bypass the manual selection by creating a pre-selected JSON if needed, 
    # but since the user wants a "player 1", we will use the interactive tracker.
    # To make it "automatic" for just 1 player, we would ideally need a non-interactive selector.
    # However, 'track_player' uses 'select_players_gui/terminal'.
    
    print(f"\n>>> Starting Tracking for video: {video_path}")
    print(">>> Please select 'Player 1' when prompted.")
    
    # Run the interactive tracking (Phase 1, 2, 3)
    # This will generate player videos in the output directory
    player_videos = run_interactive_tracking(
        video_path=video_path,
        mode="terminal", # Defaulting to terminal for simplicity
        output_dir=output_dir,
        max_players=1,
        include_black_frames=True
    )

    if not player_videos:
        print("No player videos generated. Exiting.")
        return

    # --- Phase 4: Analysis ---
    print(f"\n>>> Starting LLM Analysis for {len(player_videos)} player(s)")
    
    for v_path in player_videos:
        player_name = os.path.basename(v_path).replace(".mp4", "")
        print(f"\n=== Analyzing {player_name} ({v_path}) ===")
        
        analysis_result, cost_info = analyze_pickleball_video(v_path)
        
        if analysis_result:
            # Save individual analysis
            analysis_output = os.path.join(output_dir, f"{player_name}_analysis.json")
            with open(analysis_output, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, indent=4, ensure_ascii=False)
            
            print(f"Analysis saved to: {analysis_output}")
            print("\nSummary:")
            print(analysis_result.get("analysis_summary", "No summary available."))
            
            if cost_info:
                print(f"Cost estimated: ${cost_info['total_cost_usd']:.6f}")
        else:
            print(f"Failed to analyze {v_path}")

    print("\n>>> Pipeline Completed Successfully.")

if __name__ == "__main__":
    main()
