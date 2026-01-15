# Task Plan: player_detection_yolo

## 1. Summary

Xây dựng hệ thống sử dụng YOLO để phát hiện và **tracking players** trong video pickleball, kết hợp với perspective transform để chuyển đổi tọa độ pixel sang tọa độ thực trên sân.

**Input:**
- Video pickleball: `video/yep_pickleball.mp4` (3709 frames, 60fps)
- Tọa độ sân đã có: `app/service/court_coordinates.json`

**Output:**
- Bounding boxes của players trên mỗi frame với **consistent track ID**
- Tọa độ thực của players so với sân (đơn vị: mét)
- Video đầu ra có visual annotations
- JSON data cho mọi frame (không skip)

## 2. Assumptions / Constraints

### Assumptions:
- Camera góc cố định (đã xác nhận từ user)
- Sân pickleball tiêu chuẩn: 6.1m x 13.4m (20ft x 44ft)
- Có 2-4 players trên sân
- Players mặc trang phục khác biệt với sân

### Constraints:
- Sử dụng ultralytics YOLO (đã cài đặt: v8.4.2)
- Python 3.12+
- **Xử lý TẤT CẢ frames** (không skip)
- **Player ID phải consistent** xuyên suốt video (cần tracking)
- **Chỉ detect players trong sân** (filter người ngoài sân)

## 3. Acceptance Criteria

1. ✅ Detect được tất cả players trong video với accuracy > 90%
2. ✅ **Player ID giữ nguyên** xuyên suốt video (Player 1 luôn là Player 1)
3. ✅ **Chỉ detect players trong sân** - loại bỏ khán giả, trọng tài
4. ✅ Tọa độ court được tính từ bottom-center của bounding box
5. ✅ Output JSON chứa **tất cả frames** (3709 frames)
6. ✅ Video output có visual annotation (bounding box + court position + track ID)

## 4. Modules Breakdown

| # | Module | Objective | Owner |
|---|--------|-----------|-------|
| 1 | court_transform | Perspective transform pixel → court coordinates | coding_agent |
| 2 | player_detector | YOLO-based player detection **with ByteTrack tracking** | coding_agent |
| 3 | court_filter | **Filter detections to only players inside court** | coding_agent |
| 4 | video_processor | Main pipeline: read video → detect → track → filter → transform → output | coding_agent |
| 5 | visualization | Draw annotations on video frames | coding_agent |

## 5. Proposed Phases

### Phase 1: Core Setup (Module 1)
- Implement perspective transform using court_coordinates.json
- Define court boundary polygon for filtering
- Test with sample points

### Phase 2: Detection + Tracking (Module 2)
- Setup YOLO model for person detection
- **Integrate ByteTrack** (built-in với ultralytics) để giữ consistent ID
- Configure detection parameters (confidence, NMS)

### Phase 3: Court Filtering (Module 3)
- **Filter detections** - chỉ giữ players có foot position trong sân
- Sử dụng court polygon từ court_coordinates.json

### Phase 4: Pipeline Integration (Module 4)
- Connect modules together
- **Process ALL frames** (3709 frames)
- Save results to JSON

### Phase 5: Visualization (Module 5)
- Draw bounding boxes with **track IDs**
- Display court position
- Export annotated video

## 6. Risks / Open Questions

### Risks:
- **Occlusion**: Players có thể che nhau → tracking có thể bị switch ID
- **ID Switch**: Khi players đi gần nhau, ByteTrack có thể swap ID
- **Edge cases**: Players đứng sát biên sân có thể bị filter nhầm

### Mitigations:
- Sử dụng ByteTrack với high confidence threshold
- Cho phép buffer zone nhỏ quanh court boundary
- Log warnings khi detect > 4 players trong sân

### Resolved Questions:
- ✅ Tracking ID cố định: **CÓ** - sử dụng ByteTrack
- ✅ Output format: JSON + annotated video
- ✅ Filter người ngoài sân: **CÓ** - sử dụng court polygon
- ✅ Frame processing: **TẤT CẢ frames** (không skip)

## 7. File Structure

```
app/
├── service/
│   ├── court_coordinates.json     # ✅ Đã có
│   ├── court_transform.py         # Module 1
│   ├── player_detector.py         # Module 2
│   ├── video_processor.py         # Module 3
│   └── visualization.py           # Module 4
├── main.py                        # Entry point
output/
├── player_tracking.json           # Detection results
└── annotated_video.mp4            # Visual output
```
