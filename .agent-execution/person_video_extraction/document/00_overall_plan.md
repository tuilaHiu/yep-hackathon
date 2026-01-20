# Task Plan: person_video_extraction

## 1. Summary
Phân tích video pickleball để detect và track từng người chơi riêng biệt bằng YOLO + ByteTrack, sau đó cắt ra các video riêng chỉ chứa bounding box của từng người. Số lượng video output = số người được track trong video.

## 2. Assumptions / Constraints
- **Input video:** `yep_pickleball.mp4` (~25MB)
- **YOLO model:** YOLOv8 với class "person" (class_id=0)
- **Tracker:** ByteTrack để assign persistent ID cho từng người
- **Output size:** Kích thước cố định = max bounding box + 20% padding
- **Mất track:** Giữ frame trống (đen) khi người không xuất hiện
- **GPU:** Không phải CUDA → sử dụng CPU fallback (ultralytics tự động detect)
- **Format output:** `.mp4` (H.264/libx264)

## 3. Acceptance Criteria
- [ ] Detect được tất cả người trong video bằng YOLO
- [ ] Track từng người với ID riêng biệt xuyên suốt video
- [ ] Tạo N video output (N = số người được track)
- [ ] Mỗi video chỉ chứa 1 người với kích thước cố định
- [ ] Frame trống khi người không xuất hiện trong frame gốc
- [ ] Video output có cùng FPS với video gốc
- [ ] Tên file: `person_{track_id}.mp4`

## 4. Modules Breakdown
1) **person_tracking_detection**: Detect và track người trong video bằng YOLO + ByteTrack, lưu tracking data
2) **video_cropping**: Cắt video theo bounding box của từng người, tạo video output riêng biệt

## 5. Proposed Phases
- **Phase 1:** Implement person detection & tracking module
  - Load video, chạy YOLO detection
  - Áp dụng ByteTrack để track người
  - Lưu tracking data (track_id, frame_id, bbox) vào file JSON
  - Tính toán max bounding box cho mỗi track

- **Phase 2:** Implement video cropping module
  - Đọc tracking data từ Phase 1
  - Tính output size = max_bbox + 20% padding
  - Crop từng frame theo bbox, pad về kích thước cố định
  - Xuất video cho từng người

## 6. Risks / Open Questions
- **Performance:** Video 25MB trên CPU có thể chậm (ước tính 5-15 phút)
- **Occlusion:** Người bị che khuất có thể gây mất track → ByteTrack đã xử lý tốt trường hợp này
- **Multiple persons:** Cần xác định số người thực tế trong video để verify
