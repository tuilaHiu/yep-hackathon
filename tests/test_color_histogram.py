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
    assert hist.dtype == np.float32


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
    # Clipped region should be (50, 50, 3)
    assert cropped.shape == (50, 50, 3)
