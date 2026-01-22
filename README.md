# Yep Pickleball - Player Tracking & AI Coach Analysis

Hệ thống tích hợp theo vết người chơi (Player Tracking) và phân tích kỹ thuật bằng AI dành riêng cho môn Pickleball. Hệ thống cho phép chọn người chơi, theo vết tự động, trích xuất video riêng biệt và gửi cho Coach AI (LLM) để nhận xét kỹ thuật.

## 🚀 Luồng hoạt động (Workflow)

1.  **Selection**: Chọn người chơi cần theo dõi (qua Terminal hoặc GUI).
2.  **Tracking**: Tự động bám theo người chơi suốt video sử dụng model YOLO (Pose/Detection) kết hợp Spatial & Color Histogram.
3.  **Cropping**: Trích xuất video tập trung vào người chơi với kích thước cố định.
4.  **AI Analysis**: Gửi video đã cắt cho AI (GPT-4o/GPT-5.2) để phân tích các động tác như Forehand, Backhand, Dink... và đưa ra bài tập cải thiện.

## 🛠 Cài đặt

Dự án sử dụng `uv` để quản lý dependency.

1.  **Cài đặt môi trường**:
    ```bash
    uv sync
    ```

2.  **Cấu hình API Key**:
    Tạo file `.env` ở thư mục gốc và thêm key OpenAI của bạn (Lưu ý tên biến môi trường trong code hiện tại là `OPENAI__API_KEY`):
    ```env
    OPENAI__API_KEY=your_openai_api_key_here
    ```

## 📖 Cách chạy

### 1. Chạy toàn bộ Pipeline (Tracking + Analysis)
Đây là cách nhanh nhất để lấy cả video track và kết quả phân tích AI.
```bash
uv run python main.py --video video/your_video.mp4
```
*Mặc định script sẽ chạy ở chế độ Terminal để bạn chọn người chơi.*

### 2. Chỉ chạy Tracking & Cropping
Nếu bạn chỉ muốn trích xuất video người chơi mà không cần phân tích AI:
```bash
uv run python app/service/track_player.py --video video/your_video.mp4 --mode terminal --max-players 1 --fixed-size 300x600
```

## ⚙️ Các tham số chính (Arguments)

| Tham số | Mô tả | Mặc định |
| :--- | :--- | :--- |
| `--video` | Đường dẫn file video đầu vào | `pickleball.mp4` |
| `--output-dir`| Thư mục lưu kết quả | `output` |
| `--mode` | Chế độ chọn người: `gui` hoặc `terminal` | `terminal` |
| `--max-players`| Số lượng người chơi tối đa cần track | `1` (trong main.py) |
| `--fixed-size` | Kích thước video đầu ra (VD: `300x600`) | Tự động |

## 📁 Kết quả đầu ra (Output)

Kết quả được lưu tại thư mục `output/`:
-   `[Tên_Người_Chơi].mp4`: Video đã được cắt theo vị trí người chơi.
-   `[Tên_Người_Chơi]_analysis.json`: Kết quả phân tích chi tiết từ AI (bao gồm đánh giá lỗi và bài tập gợi ý).
-   `selected_players.json`: Thông tin tọa độ ban đầu của người chơi đã chọn.
-   `selective_tracking_data.json`: Dữ liệu tracking chi tiết qua từng frame.

## 🎥 Ví dụ
Để track và phân tích một video cụ thể:
```bash
uv run python main.py --video video/yep_pickleball_30fps.mp4
```
Sau đó làm theo hướng dẫn trong terminal để chọn ID người chơi.
