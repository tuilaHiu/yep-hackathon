# Yep Player Tracker

Hệ thống theo vết người chơi (Player Tracking) tự động cho video thể thao (ví dụ: Pickleball). Hệ thống cho phép chọn người chơi cụ thể, theo vết họ suốt video và xuất ra các video đã được cắt riêng cho từng người.

## Luồng hoạt động (Workflow)
1. **Selection**: Chọn người chơi từ một frame hình (qua giao diện GUI hoặc Terminal).
2. **Tracking**: Tự động bám theo người chơi sử dụng model YOLO và thuật toán so khớp đặc trưng (spatial + color histogram).
3. **Cropping**: Xuất video riêng biệt cho từng người chơi đã chọn.

## Cài đặt

Dự án sử dụng `uv` để quản lý dependency. Bạn có thể cài đặt môi trường bằng lệnh:

```bash
uv sync
```

Hoặc cài các thư viện cần thiết qua pip:
```bash
pip install numpy opencv-python tqdm ultralytics
```

## Cách chạy

Script chính để chạy toàn bộ pipeline là `app/service/track_player.py`.

### 1. Chế độ Giao diện (GUI - Khuyến khích)
Sử dụng chuột để click vào các khung hình người chơi và nhập tên.
```bash
python app/service/track_player.py --video your_video.mp4 --mode gui
```

### 2. Chế độ Terminal
Nhận diện người chơi và yêu cầu bạn chọn qua số thứ tự trong terminal.
```bash
python app/service/track_player.py --video your_video.mp4 --mode terminal
```

## Các tham số (Arguments)

| Tham số | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `--video` | Đường dẫn tới file video đầu vào (Bắt buộc) | - |
| `--mode` | Chế độ chọn người: `gui` hoặc `terminal` | `terminal` |
| `--output-dir` | Thư mục lưu kết quả | `output` |
| `--max-players` | Số lượng người chơi tối đa cần track | `4` |
| `--fixed-size` | Kích thước video đầu ra (VD: `200x500`) | Tự động |
| `--model` | Đường dẫn tới model YOLO (.pt) | `yolo11n.pt` |
| `--frame` | Frame index dùng để chọn người chơi ban đầu | `0` |
| `--no-black-frames` | Không chèn frame đen khi mất dấu người chơi | `False` |

## Kết quả đầu ra (Output)

Sau khi chạy xong, kết quả sẽ được lưu trong thư mục `--output-dir` (mặc định là `output/`):
- `selected_players.json`: Chứa thông tin vị trí ban đầu và tên người chơi đã chọn.
- `selective_tracking_data.json`: Chứa dữ liệu tọa độ của người chơi qua từng frame.
- `[Tên_Người_Chơi].mp4`: Các video đã cắt riêng cho từng người.

## Ví dụ nâng cao

Chạy với video cụ thể, chọn 2 người chơi qua GUI và cố định kích thước video đầu ra:
```bash
python app/service/track_player.py --video pickleball.mp4 --mode gui --max-players 2 --fixed-size 300x600
```
