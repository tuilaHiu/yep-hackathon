# Module 01: Color Histogram Extractor

## Owner
`coding_agent`

## Objective
Tạo module trích xuất và so sánh color histogram từ bounding box của người chơi.

## Dependencies
- `opencv-python` (existing)
- `numpy` (existing)

## File Location
`app/service/color_histogram.py`

## Input/Output

### Input:
- `frame`: numpy array (BGR image)
- `bbox`: dict với keys `x1, y1, x2, y2`

### Output:
- `histogram`: numpy array (normalized histogram vector)

## API Design

```python
"""
Color Histogram module for player re-identification.
"""
import cv2
import numpy as np
from typing import Dict, Tuple


def extract_color_histogram(
    frame: np.ndarray,
    bbox: Dict[str, int],
    bins_h: int = 50,
    bins_s: int = 50,
) -> np.ndarray:
    """
    Extract HSV color histogram from bounding box region.
    
    Args:
        frame: BGR image (numpy array).
        bbox: Bounding box with keys x1, y1, x2, y2.
        bins_h: Number of bins for Hue channel (0-180).
        bins_s: Number of bins for Saturation channel (0-256).
    
    Returns:
        np.ndarray: Normalized histogram vector (shape: bins_h + bins_s,).
    
    Example:
        >>> frame = cv2.imread("frame.jpg")
        >>> bbox = {"x1": 100, "y1": 100, "x2": 200, "y2": 300}
        >>> hist = extract_color_histogram(frame, bbox)
        >>> print(hist.shape)  # (100,)
    """
    pass


def compare_histograms(
    hist1: np.ndarray,
    hist2: np.ndarray,
    method: int = cv2.HISTCMP_CORREL,
) -> float:
    """
    Calculate similarity between two histograms.
    
    Args:
        hist1: First histogram vector.
        hist2: Second histogram vector.
        method: OpenCV comparison method. Options:
            - cv2.HISTCMP_CORREL: Correlation (1 = identical, -1 = opposite)
            - cv2.HISTCMP_CHISQR: Chi-Square (0 = identical, higher = different)
            - cv2.HISTCMP_INTERSECT: Intersection (higher = more similar)
            - cv2.HISTCMP_BHATTACHARYYA: Bhattacharyya (0 = identical, 1 = different)
    
    Returns:
        float: Similarity score. For CORREL method, range is [-1, 1].
    
    Example:
        >>> similarity = compare_histograms(hist1, hist2)
        >>> print(f"Similarity: {similarity:.2f}")
    """
    pass


def update_histogram_ema(
    reference_hist: np.ndarray,
    new_hist: np.ndarray,
    alpha: float = 0.1,
) -> np.ndarray:
    """
    Update reference histogram using Exponential Moving Average.
    
    This helps the reference histogram adapt to gradual appearance
    changes (lighting, pose) while remaining stable.
    
    Args:
        reference_hist: Current reference histogram.
        new_hist: New histogram from current frame.
        alpha: EMA weight for new histogram (0-1). 
               Lower = more stable, higher = more adaptive.
    
    Returns:
        np.ndarray: Updated histogram.
    
    Formula:
        updated = (1 - alpha) * reference + alpha * new
    
    Example:
        >>> ref_hist = extract_color_histogram(frame1, bbox1)
        >>> new_hist = extract_color_histogram(frame2, bbox2)
        >>> ref_hist = update_histogram_ema(ref_hist, new_hist, alpha=0.1)
    """
    pass


def crop_bbox_from_frame(
    frame: np.ndarray,
    bbox: Dict[str, int],
    padding: float = 0.0,
) -> np.ndarray:
    """
    Crop bounding box region from frame with optional padding.
    
    Args:
        frame: BGR image.
        bbox: Bounding box with keys x1, y1, x2, y2.
        padding: Padding ratio (0.0 = no padding, 0.1 = 10% padding).
    
    Returns:
        np.ndarray: Cropped image region.
    """
    pass
```

## Implementation Details

### 1. Color Space: HSV
Sử dụng HSV thay vì BGR vì:
- **Hue (H)**: Màu sắc - ít bị ảnh hưởng bởi ánh sáng
- **Saturation (S)**: Độ bão hòa - giúp phân biệt màu
- **Value (V)**: Độ sáng - KHÔNG dùng vì sensitive với lighting

```python
# Convert to HSV
hsv = cv2.cvtColor(cropped_region, cv2.COLOR_BGR2HSV)

# Extract H and S channels only (ignore V)
h_channel = hsv[:, :, 0]  # Range: 0-180
s_channel = hsv[:, :, 1]  # Range: 0-256
```

### 2. Histogram Calculation

```python
# Calculate histograms
hist_h = cv2.calcHist([hsv], [0], None, [bins_h], [0, 180])
hist_s = cv2.calcHist([hsv], [1], None, [bins_s], [0, 256])

# Normalize
hist_h = cv2.normalize(hist_h, hist_h, 0, 1, cv2.NORM_MINMAX)
hist_s = cv2.normalize(hist_s, hist_s, 0, 1, cv2.NORM_MINMAX)

# Concatenate into single vector
histogram = np.concatenate([hist_h.flatten(), hist_s.flatten()])
```

### 3. Region Selection (Optional Enhancement)
Chỉ lấy phần giữa của bbox để tránh background:

```python
# Crop center region (60% of bbox) to avoid background
h, w = cropped.shape[:2]
margin_x = int(w * 0.2)
margin_y = int(h * 0.1)  # Less margin on top (head area)
center_region = cropped[margin_y:h-margin_y, margin_x:w-margin_x]
```

## Acceptance Criteria

- [ ] `extract_color_histogram()` returns normalized vector of shape `(bins_h + bins_s,)`
- [ ] `compare_histograms()` returns float in range `[-1, 1]` for CORREL method
- [ ] `update_histogram_ema()` returns same shape as input histogram
- [ ] Handle edge cases: bbox out of frame, empty region
- [ ] All functions have type hints and docstrings

## Unit Tests

```python
import numpy as np
import cv2
import pytest
from app.service.color_histogram import (
    extract_color_histogram,
    compare_histograms,
    update_histogram_ema,
    crop_bbox_from_frame,
)


def test_extract_color_histogram_shape():
    """Test histogram has correct shape."""
    # Create dummy frame (100x100 blue image)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:, :] = (255, 0, 0)  # BGR blue
    
    bbox = {"x1": 10, "y1": 10, "x2": 90, "y2": 90}
    hist = extract_color_histogram(frame, bbox, bins_h=50, bins_s=50)
    
    assert hist.shape == (100,)  # 50 + 50 bins
    assert hist.dtype == np.float32 or hist.dtype == np.float64


def test_extract_color_histogram_normalized():
    """Test histogram is normalized."""
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    bbox = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    
    hist = extract_color_histogram(frame, bbox)
    
    # For normalized histogram, max should be <= 1
    assert hist.max() <= 1.0
    assert hist.min() >= 0.0


def test_compare_histograms_identical():
    """Test identical histograms have similarity 1.0."""
    hist1 = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    hist2 = hist1.copy()
    
    similarity = compare_histograms(hist1, hist2)
    
    assert similarity == pytest.approx(1.0, abs=0.001)


def test_compare_histograms_different():
    """Test different histograms have lower similarity."""
    hist1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    hist2 = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    
    similarity = compare_histograms(hist1, hist2)
    
    assert similarity < 0.5  # Should be low


def test_update_histogram_ema():
    """Test EMA update formula."""
    ref = np.array([1.0, 0.0], dtype=np.float32)
    new = np.array([0.0, 1.0], dtype=np.float32)
    alpha = 0.2
    
    updated = update_histogram_ema(ref, new, alpha)
    
    expected = (1 - alpha) * ref + alpha * new
    np.testing.assert_array_almost_equal(updated, expected)


def test_crop_bbox_from_frame():
    """Test bbox cropping."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[20:80, 30:70] = (255, 255, 255)  # White region
    
    bbox = {"x1": 30, "y1": 20, "x2": 70, "y2": 80}
    cropped = crop_bbox_from_frame(frame, bbox)
    
    assert cropped.shape == (60, 40, 3)
    assert cropped.mean() == 255  # All white


def test_crop_bbox_handles_out_of_bounds():
    """Test cropping handles bbox partially outside frame."""
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    bbox = {"x1": -10, "y1": -10, "x2": 50, "y2": 50}
    cropped = crop_bbox_from_frame(frame, bbox)
    
    # Should not raise error, should return valid region
    assert cropped.shape[0] > 0 and cropped.shape[1] > 0
```

## Edge Cases to Handle

1. **Bbox out of frame**: Clip to frame boundaries
2. **Empty bbox**: Return None or raise ValueError
3. **Very small bbox**: May produce unreliable histogram
4. **Grayscale frame**: Convert to BGR first if needed
