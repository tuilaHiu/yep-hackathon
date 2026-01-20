# Module 05: Main Integration & CLI

## Owner
`coding_agent`

## Objective
Tạo script chính tích hợp tất cả modules, cung cấp CLI thân thiện với options cho cả GUI và Terminal mode.

## Dependencies
- Module 01: `player_selector_gui.py`
- Module 02: `player_selector_terminal.py`
- Module 03: `selective_tracker.py`
- Module 04: `named_video_cropper.py`

## Input
- Video file path
- Mode selection (gui/terminal)
- Optional: config file

## Output
- Individual player videos: `{player_name}.mp4`
- Tracking data: `selective_tracking_data.json`
- Selection data: `selected_players.json`

## Acceptance Criteria
- [ ] Single entry point cho toàn bộ pipeline
- [ ] CLI với `--mode gui|terminal` option
- [ ] Progress reporting cho từng phase
- [ ] Error handling và recovery
- [ ] Config file support (optional)

## Technical Design

### 1. CLI Interface

```bash
# Full pipeline with GUI
python app/service/track_player.py \
    --video yep_pickleball.mp4 \
    --mode gui \
    --output-dir output/

# Full pipeline with Terminal
python app/service/track_player.py \
    --video yep_pickleball.mp4 \
    --mode terminal \
    --output-dir output/

# Resume from selection (skip step 1)
python app/service/track_player.py \
    --video yep_pickleball.mp4 \
    --selected selected_players.json \
    --output-dir output/

# Resume from tracking (skip step 1 & 2)
python app/service/track_player.py \
    --video yep_pickleball.mp4 \
    --tracking selective_tracking_data.json \
    --output-dir output/
```

### 2. Main Function

```python
def run_interactive_tracking(
    video_path: str,
    mode: str = "gui",  # "gui" or "terminal"
    output_dir: str = "output/",
    selected_players_path: str | None = None,  # Skip selection if provided
    tracking_data_path: str | None = None,     # Skip tracking if provided
    include_black_frames: bool = True,
    max_players: int = 4,
) -> list[str]:
    """
    Run the full interactive player tracking pipeline.
    
    Args:
        video_path: Path to input video
        mode: Selection mode ("gui" or "terminal")
        output_dir: Directory for all outputs
        selected_players_path: Pre-existing selection (skip step 1)
        tracking_data_path: Pre-existing tracking (skip steps 1 & 2)
        include_black_frames: Include black frames for missing detections
        max_players: Maximum number of players to track
    
    Returns:
        list[str]: Paths to generated video files
    """
```

### 3. Pipeline Steps

```
┌────────────────────────────────────────────────────────┐
│  STEP 1: Player Selection                              │
│  ├─ GUI Mode → player_selector_gui.py                 │
│  └─ Terminal Mode → player_selector_terminal.py       │
│  Output: selected_players.json                         │
├────────────────────────────────────────────────────────┤
│  STEP 2: Selective Tracking                            │
│  └─ selective_tracker.py                              │
│  Output: selective_tracking_data.json                  │
├────────────────────────────────────────────────────────┤
│  STEP 3: Video Cropping                                │
│  └─ named_video_cropper.py                            │
│  Output: {player_name}.mp4 for each player            │
└────────────────────────────────────────────────────────┘
```

### 4. Error Handling

```python
def run_with_recovery():
    try:
        # Step 1
        selected = select_players(...)
        save_checkpoint("selected_players.json", selected)
        
        # Step 2
        tracking = run_tracking(...)
        save_checkpoint("tracking_data.json", tracking)
        
        # Step 3
        videos = crop_videos(...)
        
    except KeyboardInterrupt:
        print("Interrupted. Progress saved. Resume with --selected or --tracking")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Resume from last checkpoint using --selected or --tracking")
```

## File Location
`app/service/track_player.py`

## CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--video` | str | required | Path to input video |
| `--mode` | str | "terminal" | Selection mode: "gui" or "terminal" |
| `--output-dir` | str | "output/" | Output directory |
| `--selected` | str | None | Pre-existing selection JSON |
| `--tracking` | str | None | Pre-existing tracking JSON |
| `--max-players` | int | 4 | Maximum players to select |
| `--no-black-frames` | flag | False | Skip black frames for missing detections |
| `--frame` | int | 0 | Frame index for selection |

## Example Usage

```bash
# Typical workflow
python app/service/track_player.py --video yep_pickleball.mp4 --mode terminal

# Output structure
output/
├── selected_players.json
├── selective_tracking_data.json
├── nguyen.mp4
└── tran.mp4
```

## Testing

```python
def test_run_interactive_tracking_terminal():
    # Integration test với mocked input
    pass

def test_resume_from_selection():
    # Test resuming from existing selection
    pass

def test_resume_from_tracking():
    # Test resuming from existing tracking
    pass
```
