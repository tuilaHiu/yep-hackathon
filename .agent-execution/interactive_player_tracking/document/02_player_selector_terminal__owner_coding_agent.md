# Module 02: Player Selector Terminal

## Owner
`coding_agent`

## Objective
Tạo giao diện Terminal cho phép user nhập số thứ tự và tên người chơi cần track.

## Dependencies
- `opencv-python`: Hiển thị frame (read-only)
- `ultralytics`: YOLO detection
- `numpy`: Array operations

## Input
- Video file path (`str`)
- Frame index để hiển thị (default: 0)

## Output
- `selected_players.json` (cùng format với GUI module)

## Acceptance Criteria
- [ ] Hiển thị frame với các bbox được đánh số
- [ ] In ra terminal danh sách các detection (số thứ tự + bbox info)
- [ ] User nhập số thứ tự người cần track (VD: "1,3" hoặc "1 3")
- [ ] Prompt nhập tên cho từng người đã chọn
- [ ] Xác nhận và lưu selection
- [ ] Hiển thị preview với các người đã chọn được highlight

## Technical Design

### 1. Terminal Flow
```
=== PLAYER SELECTION ===
Video: yep_pickleball.mp4
Frame: 0

Detected persons:
  [1] Position: (100, 200) - Size: 100x200
  [2] Position: (300, 200) - Size: 90x180
  [3] Position: (500, 200) - Size: 110x210
  [4] Position: (700, 200) - Size: 95x190

Enter player numbers to track (comma separated): 1, 3

Enter name for Player 1: Nguyen
Enter name for Player 3: Tran

--- Selection Summary ---
  1. Nguyen - BBox(100, 200, 200, 400)
  3. Tran - BBox(500, 200, 610, 410)

Confirm selection? (y/n): y
Selection saved to: selected_players.json
```

### 2. Key Functions

```python
def select_players_terminal(
    video_path: str,
    frame_index: int = 0,
    max_players: int = 4,
    output_path: str | None = None,
    show_preview: bool = True
) -> dict:
    """
    Terminal-based player selection.
    
    Args:
        video_path: Path to video file
        frame_index: Frame to display for selection
        max_players: Maximum number of players to select
        output_path: Path to save selection JSON
        show_preview: Whether to show OpenCV preview window
    
    Returns:
        dict: Selected players data
    """
```

### 3. Input Parsing
```python
def parse_player_input(input_str: str, max_id: int) -> list[int]:
    """
    Parse user input for player IDs.
    
    Accepts formats:
    - "1,2,3"
    - "1 2 3"
    - "1, 2, 3"
    - "1"
    
    Returns:
        list[int]: Valid player IDs (1-indexed)
    """
```

## File Location
`app/service/player_selector_terminal.py`

## CLI Usage
```bash
python app/service/player_selector_terminal.py \
    --video yep_pickleball.mp4 \
    --frame 0 \
    --output selected_players.json \
    --no-preview  # Optional: skip OpenCV window
```

## Edge Cases
- Input không hợp lệ → Re-prompt với error message
- ID không tồn tại → Warning, bỏ qua ID đó
- Chọn quá nhiều người → Warning, chỉ lấy max_players đầu tiên
- Tên trống → Dùng default "Player_{n}"
- User cancel (Ctrl+C) → Exit gracefully, không save

## Testing
```python
def test_parse_player_input():
    assert parse_player_input("1,2,3", 5) == [1, 2, 3]
    assert parse_player_input("1 2 3", 5) == [1, 2, 3]
    assert parse_player_input("1, 2, 3", 5) == [1, 2, 3]
    assert parse_player_input("1", 5) == [1]
    assert parse_player_input("6", 5) == []  # Out of range
    assert parse_player_input("abc", 5) == []  # Invalid

def test_select_players_terminal_dry_run():
    # Test with mocked input
    pass
```
