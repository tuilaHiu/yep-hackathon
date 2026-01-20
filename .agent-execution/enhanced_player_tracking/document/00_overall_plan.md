# Task Plan: enhanced_player_tracking

## 1. Summary
Cải thiện hệ thống tracking người chơi bằng cách kết hợp **Spatial Matching (IOU + Center Distance)** và **Color Histogram Matching**. Mục tiêu là giải quyết vấn đề "đổi người" khi ByteTrack mất track và re-match sai người.

## 2. Problem Statement

### Vấn đề hiện tại:
- Khi ByteTrack mất track (do occlusion hoặc detection fail), code hiện tại chỉ dùng **IOU matching** để re-identify
- IOU matching fail khi:
  1. Người di chuyển nhanh (bbox mới không overlap với bbox cũ)
  2. Có nhiều người gần nhau (match sai người)
  3. Mất track quá lâu (vị trí thay đổi nhiều)

### Giải pháp đề xuất:
Hybrid approach: **Spatial + Color Histogram**
1. **Spatial filtering**: Lọc candidates bằng center distance (loại bỏ người ở quá xa)
2. **Color matching**: Trong candidates, chọn người có histogram similarity cao nhất

## 3. Assumptions / Constraints

### Inputs:
- Existing codebase: `app/service/selective_tracker.py`
- Video file: Pickleball video với 1-4 người chơi
- Selected players JSON với initial bbox

### Constraints:
- **Không thêm dependencies mới**: Chỉ dùng `opencv-python`, `numpy` (đã có)
- **Không cần GPU**: Color histogram chạy trên CPU
- **Backward compatible**: Giữ nguyên API của `run_selective_tracking()`

### Assumptions:
- Người chơi mặc áo có màu khác nhau (đặc biệt là áo đen vs áo trắng)
- Video có quality đủ tốt để extract color histogram
- Ánh sáng không thay đổi quá đột ngột trong video

## 4. Acceptance Criteria

### Core Functionality:
- [ ] Extract color histogram cho người được chọn ở frame đầu
- [ ] Lưu reference histogram cho mỗi player
- [ ] Khi mất track, lọc candidates bằng center distance
- [ ] Trong candidates, match bằng color histogram similarity
- [ ] Cập nhật reference histogram định kỳ (EMA update)

### Quality Metrics:
- [ ] Giảm số lần "đổi người" xuống 0 hoặc gần 0
- [ ] Không làm chậm tracking quá 20%
- [ ] Track liên tục hơn (ít missing frames hơn)

### Testing:
- [ ] Unit test cho `extract_color_histogram()`
- [ ] Unit test cho `compare_histograms()`
- [ ] Unit test cho `hybrid_rematch()`
- [ ] Integration test với video thực tế

## 5. Modules Breakdown

1) **color_histogram_extractor**: Trích xuất và so sánh color histogram từ bounding box
2) **enhanced_tracker**: Cập nhật `selective_tracker.py` với hybrid matching logic

## 6. Proposed Phases

### Phase 1: Color Histogram Module
- Implement `extract_color_histogram()` function
- Implement `compare_histograms()` function
- Unit tests

### Phase 2: Enhanced Tracker
- Modify `selective_tracker.py` để lưu reference histogram
- Implement `hybrid_rematch()` function
- Integrate vào tracking loop
- Update tracking state structure

### Phase 3: Testing & Tuning
- Test với video pickleball
- Tune thresholds (distance, similarity)
- Validate không còn "đổi người"

## 7. Technical Design Overview

### Data Flow:
```
Frame N (Selection):
┌─────────────────────────────────────────────────────────┐
│  1. Detect người được chọn                              │
│  2. Crop bbox từ frame                                  │
│  3. Extract color histogram → reference_histogram       │
│  4. Lưu vào player_state                               │
└─────────────────────────────────────────────────────────┘

Frame N+k (Lost Track):
┌─────────────────────────────────────────────────────────┐
│  1. ByteTrack mất track_id của người X                 │
│  2. Tính max_distance = base_speed × frames_lost       │
│  3. Lọc detections có center_distance < max_distance   │
│  4. Với mỗi candidate:                                 │
│     - Crop bbox                                        │
│     - Extract histogram                                │
│     - Compare với reference_histogram                  │
│  5. Chọn candidate có similarity cao nhất              │
│  6. Update reference_histogram với EMA                 │
└─────────────────────────────────────────────────────────┘
```

### Key Parameters:
| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_speed` | 5.0 | Pixels per frame movement estimate |
| `max_distance_cap` | 500 | Maximum search radius (pixels) |
| `histogram_bins_h` | 50 | Number of bins for Hue channel |
| `histogram_bins_s` | 50 | Number of bins for Saturation channel |
| `similarity_threshold` | 0.5 | Minimum histogram correlation for match |
| `ema_alpha` | 0.1 | Exponential moving average for histogram update |

## 8. Risks / Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Color histogram fail với lighting changes | Medium | High | Use HSV (less sensitive to lighting), add histogram normalization |
| Người mặc áo cùng màu | Low | High | Combine với spatial distance as tiebreaker |
| Performance degradation | Low | Medium | Cache histograms, only compute when needed |
| Histogram không stable | Medium | Medium | Use EMA update để smooth histogram |

## 9. Files to Modify/Create

### New Files:
- `app/service/color_histogram.py` - Histogram extraction module

### Modified Files:
- `app/service/selective_tracker.py` - Add hybrid matching

## 10. Dependencies
- `opencv-python` (existing) - For histogram calculation
- `numpy` (existing) - For array operations

No new dependencies required.
