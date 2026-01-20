# Task Plan: interactive_player_tracking

## 1. Summary
Xây dựng hệ thống cho phép user **chủ động chọn và gán nhãn** người chơi cần track trên frame đầu tiên của video, sau đó hệ thống chỉ track những người đã được chọn. Hỗ trợ cả 2 phương thức input: **GUI (click to select)** và **Terminal (nhập ID)**. Output là các video cropped riêng biệt cho từng người chơi đã chọn.

## 2. Assumptions / Constraints

### Inputs:
- **Video file:** `yep_pickleball.mp4` hoặc video pickleball khác
- **YOLO model:** YOLOv8 (`yolov8n.pt`) để detect người
- **Tracker:** ByteTrack cho persistent tracking

### Constraints:
- **Số người tối đa:** 4 người
- **Số người hiện tại cần track:** 1 người (có thể mở rộng)
- **Tên người chơi:** Cần gán tên cụ thể (VD: "Nguyen", "Player_A")
- **Environment:** Python >= 3.12, CPU (không có CUDA)
- **Output format:** `.mp4` (H.264/libx264)

### Assumptions:
- User sẽ chọn người chơi trên frame đầu tiên hoặc frame bất kỳ
- YOLO có thể detect được người chơi cần track trên frame chọn
- Người chơi được chọn sẽ xuất hiện trong phần lớn video

## 3. Acceptance Criteria

### Core Features:
- [ ] Hiển thị frame và các bounding box được YOLO detect
- [ ] User có thể chọn người chơi bằng GUI (click) hoặc Terminal (nhập số)
- [ ] User có thể gán tên cụ thể cho mỗi người chơi
- [ ] Hệ thống track chỉ những người đã được chọn
- [ ] Output video được đặt tên theo tên người chơi (VD: `nguyen.mp4`)

### GUI Mode:
- [ ] Hiển thị frame với các bbox được đánh số
- [ ] Click để chọn/bỏ chọn người
- [ ] Popup hoặc input để nhập tên người chơi
- [ ] Nút xác nhận khi chọn xong

### Terminal Mode:
- [ ] Hiển thị frame với các bbox được đánh số
- [ ] Nhập số thứ tự người cần track
- [ ] Nhập tên cho người đã chọn
- [ ] Xác nhận và tiếp tục

### Quality:
- [ ] Video output có cùng FPS với video gốc
- [ ] Bbox size cố định = max_bbox + 20% padding
- [ ] Frame đen khi người mất track

## 4. Modules Breakdown

1) **player_selector_gui**: Giao diện GUI cho phép user click để chọn người chơi và gán tên
2) **player_selector_terminal**: Giao diện Terminal cho phép user nhập số và tên người chơi
3) **selective_tracker**: Module tracking chỉ những người đã được chọn, maintain ID assignment
4) **named_video_cropper**: Crop video và đặt tên file theo tên người chơi

## 5. Proposed Phases

### Phase 1: Player Selection Module
- Implement player_selector_gui.py
- Implement player_selector_terminal.py
- Output: `selected_players.json` (list người đã chọn + tên)

### Phase 2: Selective Tracking Module
- Re-use logic từ person_tracker.py
- Add logic filter chỉ track người đã chọn
- Match selected bbox với YOLO detections qua IOU
- Output: `selective_tracking_data.json`

### Phase 3: Named Video Cropper
- Modify video_cropper.py để đọc player names
- Output files với tên người chơi: `{player_name}.mp4`

### Phase 4: Integration & CLI
- Tạo main script tích hợp tất cả modules
- CLI với options: `--mode gui|terminal`

## 6. Risks / Open Questions

### Risks:
- **Re-ID khi mất track:** Nếu ByteTrack assign ID mới sau khi mất track, cần logic re-match
- **Occlusion:** Người chơi bị che khuất có thể gây mất track
- **Performance:** Video dài trên CPU có thể chậm (5-15 phút)

### Open Questions:
- ~~Số người tối đa cần track?~~ → **4 người (hiện tại 1)**
- ~~Cần tên cụ thể hay chỉ ID?~~ → **Cần tên cụ thể**
- ~~GUI hay Terminal?~~ → **Cả 2**

## 7. Dependencies & Existing Code

### Có thể tái sử dụng:
- `app/service/person_tracker.py`: Logic YOLO + ByteTrack
- `app/service/video_cropper.py`: Logic crop và pad frame
- `app/service/tracking_output/tracking_data.json`: Reference data đã có

### Cần thêm:
- OpenCV GUI callbacks (`cv2.setMouseCallback`)
- IOU matching logic cho player re-identification
