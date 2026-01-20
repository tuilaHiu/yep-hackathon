from app.service.selective_tracker import calculate_iou, match_bbox_to_detections


def test_calculate_iou():
    # Perfect overlap
    box1 = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    box2 = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    assert calculate_iou(box1, box2) == 1.0

    # No overlap
    box3 = {"x1": 200, "y1": 200, "x2": 300, "y2": 300}
    assert calculate_iou(box1, box3) == 0.0

    # Partial overlap (50x50 intersection = 2500)
    # Area1 = 10000, Area2 = 10000
    # Union = 10000 + 10000 - 2500 = 17500
    # IOU = 2500 / 17500 = 1/7 ~= 0.142857
    box4 = {"x1": 50, "y1": 50, "x2": 150, "y2": 150}
    iou = calculate_iou(box1, box4)
    assert 0.14 < iou < 0.15


def test_match_bbox_to_detections():
    target = {"x1": 100, "y1": 100, "x2": 200, "y2": 200}
    detections = [
        {"bbox": [0, 0, 50, 50]},       # No overlap
        {"bbox": [90, 90, 190, 190]},   # High overlap
        {"bbox": [150, 150, 250, 250]}  # Partial
    ]
    
    # Test best match
    result = match_bbox_to_detections(target, detections, iou_threshold=0.3)
    assert result == 1

    # Test thresholding
    result_low_thresh = match_bbox_to_detections(target, detections, iou_threshold=0.8)
    assert result_low_thresh is None
