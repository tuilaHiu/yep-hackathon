# Module 01: Player Selector GUI

## Owner
`coding_agent`

## Objective
Tạo giao diện GUI cho phép user click để chọn người chơi cần track và gán tên cụ thể cho từng người.

## Dependencies
- `opencv-python`: Hiển thị frame và xử lý mouse events
- `ultralytics`: YOLO detection
- `numpy`: Array operations

## Input
- Video file path (`str`)
- Frame index để hiển thị (default: 0)

## Output
- `selected_players.json`:
```json
{
  "video_source": "yep_pickleball.mp4",
  "selection_frame": 0,
  "players": [
    {
      "selection_id": 1,
      "name": "Nguyen",
      "initial_bbox": {"x1": 100, "y1": 200, "x2": 200, "y2": 400}
    }
  ]
}
```

## Acceptance Criteria
- [ ] Hiển thị frame đầu tiên với tất cả YOLO detections
- [ ] Mỗi detection được đánh số thứ tự (1, 2, 3...)
- [ ] User click vào bbox để chọn (highlight màu xanh)
- [ ] Click lại để bỏ chọn (unhighlight)
- [ ] Popup input để nhập tên người chơi sau khi click
- [ ] Hiển thị tên đã nhập bên cạnh bbox
- [ ] Nhấn 'S' hoặc Enter để save và thoát
- [ ] Nhấn 'Q' hoặc Esc để cancel
- [ ] Giới hạn tối đa 4 người được chọn

## Technical Design

### 1. GUI Flow
```
┌─────────────────────────────────────────────┐
│  Frame hiển thị với YOLO detections         │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐   │
│  │   1   │ │   2   │ │   3   │ │   4   │   │
│  └───────┘ └───────┘ └───────┘ └───────┘   │
│                                             │
│  [Click vào số để chọn]                     │
│  [Nhập tên trong terminal hoặc popup]      │
│                                             │
│  Selected: 1-Nguyen, 3-Tran                │
│  Press 'S' to save, 'Q' to quit            │
└─────────────────────────────────────────────┘
```

### 2. Key Functions

```python
def select_players_gui(
    video_path: str,
    frame_index: int = 0,
    max_players: int = 4,
    output_path: str | None = None
) -> dict:
    """
    GUI để chọn người chơi.
    
    Returns:
        dict: Selected players data
    """
```

### 3. Mouse Callback Logic
```python
def on_mouse_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if click inside any bbox
        for i, bbox in enumerate(detections):
            if is_point_in_bbox(x, y, bbox):
                toggle_selection(i)
                prompt_player_name(i)
                break
```

### 4. Keyboard Controls
| Key | Action |
|-----|--------|
| `S` or `Enter` | Save selection và thoát |
| `Q` or `Esc` | Cancel và thoát |
| `R` | Reset selection |
| `N` | Next frame |
| `P` | Previous frame |

## File Location
`app/service/player_selector_gui.py`

## CLI Usage
```bash
python app/service/player_selector_gui.py \
    --video yep_pickleball.mp4 \
    --frame 0 \
    --output selected_players.json
```

## Edge Cases
- Không có person nào được detect → Hiển thị message, cho phép chuyển frame
- User chọn quá 4 người → Hiển thị warning, không cho chọn thêm
- User không nhập tên → Dùng default "Player_{n}"
- Window bị close bất ngờ → Không save, return None

## Testing
```python
def test_player_selector_gui():
    # Manual test - cần human interaction
    pass

def test_is_point_in_bbox():
    bbox = {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
    assert is_point_in_bbox(150, 150, bbox) == True
    assert is_point_in_bbox(50, 50, bbox) == False
```
