"""
Color Histogram module for player re-identification.
"""
import cv2
import numpy as np
from typing import Dict


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
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

    bw = x2 - x1
    bh = y2 - y1

    if padding > 0:
        x1_p = int(max(0, x1 - bw * padding))
        y1_p = int(max(0, y1 - bh * padding))
        x2_p = int(min(w, x2 + bw * padding))
        y2_p = int(min(h, y2 + bh * padding))
    else:
        x1_p = int(max(0, x1))
        y1_p = int(max(0, y1))
        x2_p = int(min(w, x2))
        y2_p = int(min(h, y2))

    return frame[y1_p:y2_p, x1_p:x2_p]


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
    """
    cropped = crop_bbox_from_frame(frame, bbox)
    if cropped.size == 0:
        return np.zeros(bins_h + bins_s, dtype=np.float32)

    # Convert to HSV
    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)

    # Optional Enhancement: Only take part of the bbox to avoid background
    # Crop center region (60% of width, 80% of height)
    ch, cw = hsv.shape[:2]
    margin_x = int(cw * 0.2)
    margin_y = int(ch * 0.1)
    
    # Ensure indices are valid
    y1, y2 = margin_y, max(margin_y + 1, ch - margin_y)
    x1, x2 = margin_x, max(margin_x + 1, cw - margin_x)
    
    center_region_hsv = hsv[y1:y2, x1:x2]

    # Calculate histograms for H and S channels from the center region
    hist_h = cv2.calcHist([center_region_hsv], [0], None, [bins_h], [0, 180])
    hist_s = cv2.calcHist([center_region_hsv], [1], None, [bins_s], [0, 256])

    # Normalize each channel separately
    cv2.normalize(hist_h, hist_h, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist_s, hist_s, 0, 1, cv2.NORM_MINMAX)

    # Clip to avoid float precision issues (sometimes NORM_MINMAX gives -1e-9)
    hist_h = np.clip(hist_h, 0, 1)
    hist_s = np.clip(hist_s, 0, 1)

    # Concatenate into single vector
    histogram = np.concatenate([hist_h.flatten(), hist_s.flatten()])
    return histogram.astype(np.float32)


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
        float: Similarity score.
    """
    return float(cv2.compareHist(hist1.astype(np.float32), hist2.astype(np.float32), method))


def update_histogram_ema(
    reference_hist: np.ndarray,
    new_hist: np.ndarray,
    alpha: float = 0.1,
) -> np.ndarray:
    """
    Update reference histogram using Exponential Moving Average.

    Args:
        reference_hist: Current reference histogram.
        new_hist: New histogram from current frame.
        alpha: EMA weight for new histogram (0-1).

    Returns:
        np.ndarray: Updated histogram.
    """
    return (1 - alpha) * reference_hist + alpha * new_hist
