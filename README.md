# Yep Pickleball - Player Tracking & AI Coach Analysis

Hệ thống tích hợp theo vết người chơi (Player Tracking) và phân tích kỹ thuật bằng AI dành riêng cho môn Pickleball. Hệ thống cho phép chọn người chơi, theo vết tự động, trích xuất video riêng biệt và gửi cho Coach AI (LLM) để nhận xét kỹ thuật.

## 🚀 Luồng hoạt động (Workflow)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Detection  │────▶│  Selection  │────▶│  Tracking   │────▶│ AI Analysis │
│   (YOLO)    │     │  (Terminal) │     │ & Cropping  │     │  (GPT-5.2)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │                   │
      ▼                    ▼                   ▼                   ▼
 📸 detected_all.png  📸 selected.png   🎬 player.mp4     📄 analysis.json
```

1.  **Detection**: YOLO phát hiện tất cả người trong frame đầu tiên
2.  **Selection**: Chọn người chơi cần theo dõi qua Terminal (xem ảnh screenshot để biết ID)
3.  **Tracking**: Tự động bám theo người chơi suốt video sử dụng YOLO + Spatial & Color Histogram
4.  **Cropping**: Trích xuất video tập trung vào người chơi với kích thước cố định
5.  **AI Analysis**: Gửi video đã cắt cho AI (GPT-5.2) để phân tích kỹ thuật

## 🛠 Cài đặt

Dự án sử dụng `uv` để quản lý dependency.

1.  **Cài đặt môi trường**:
    ```bash
    uv sync
    ```

2.  **Cấu hình API Key**:
    Tạo file `.env` ở thư mục gốc và thêm key OpenAI:
    ```env
    OPENAI__API_KEY=your_openai_api_key_here
    ```

## 📖 Cách chạy

### 1. Chạy toàn bộ Pipeline (Tracking + Analysis)
```bash
uv run python main.py --video pickleball.mp4
```

**Quy trình chọn người chơi (Terminal-only):**

```
1. Script tự động detect tất cả người trong video
2. 📸 Lưu ảnh: output/pickleball_detected_all_frame0.png (tất cả người - màu ĐỎ)
3. 👉 Mở ảnh để xem ID của từng người
4. Nhập ID người chơi muốn track (VD: 1)
5. Nhập tên người chơi (VD: Player_1)
6. Confirm selection (y/n)
7. 📸 Lưu ảnh: output/pickleball_selected_players_frame0.png (người đã chọn - màu XANH)
8. Bắt đầu tracking → cropping → AI analysis
```

### 2. Chỉ chạy Tracking & Cropping (không AI)
```bash
uv run python app/service/track_player.py --video pickleball.mp4 --max-players 1 --fixed-size 300x600
```

## ⚙️ Các tham số chính (Arguments)

| Tham số | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `--video` | Đường dẫn file video đầu vào | `pickleball.mp4` |
| `--output-dir`| Thư mục lưu kết quả | `output` |
| `--max-players`| Số lượng người chơi tối đa cần track | `1` |
| `--fixed-size` | Kích thước video đầu ra (VD: `300x600`) | Tự động |

## 📁 Kết quả đầu ra (Output)

Kết quả được lưu tại thư mục `output/`:

| File | Mô tả |
| :--- | :--- |
| `pickleball_detected_all_frame0.png` | 📸 Screenshot tất cả người được detect (RED boxes) |
| `pickleball_selected_players_frame0.png` | 📸 Screenshot người đã chọn (GREEN boxes) |
| `[Tên_Người_Chơi].mp4` | 🎬 Video đã cắt theo vị trí người chơi |
| `[Tên_Người_Chơi]_analysis.json` | 📄 Kết quả phân tích từ AI |
| `selected_players.json` | Thông tin tọa độ ban đầu của người chơi đã chọn |
| `selective_tracking_data.json` | Dữ liệu tracking chi tiết qua từng frame |

## 🎥 Ví dụ

```bash
# Track và phân tích video
uv run python main.py --video video/yep_pickleball_30fps.mp4

# Xem kết quả
ls output/
# pickleball_detected_all_frame0.png   <- Ảnh tất cả người (RED)
# pickleball_selected_players_frame0.png <- Ảnh người đã chọn (GREEN)
# Player_1.mp4                          <- Video cropped
# Player_1_analysis.json                <- Phân tích AI
```

## 📝 Ghi chú

- Hệ thống sử dụng **Terminal-only mode** - không có cửa sổ GUI popup
- 2 ảnh screenshot được tự động lưu để giúp bạn xác định ID người chơi
- Mở file `*_detected_all_*.png` để xem toàn bộ người được detect với ID
