import pytest
from app.service.court_transform import CourtTransform
import json
import os

# Create a dummy config file for testing
@pytest.fixture
def court_config_file(tmp_path):
    config = {
        "court_corners": {
            "top_left": [722, 453],
            "top_right": [1180, 456],
            "bottom_right": [317, 967],
            "bottom_left": [1607, 960]
        }
    }
    file_path = tmp_path / "test_court_config.json"
    with open(file_path, "w") as f:
        json.dump(config, f)
    return str(file_path)

def test_pixel_to_court_corners(court_config_file):
    transform = CourtTransform(court_config_file)
    
    # Test top-left corner maps to (0, 0)
    cx, cy = transform.pixel_to_court(722, 453)
    assert abs(cx - 0) < 0.1
    assert abs(cy - 0) < 0.1
    
    # Test top-right corner maps to (6.1, 0)
    cx, cy = transform.pixel_to_court(1180, 456)
    assert abs(cx - 6.1) < 0.1
    assert abs(cy - 0) < 0.1

    # Test bottom-left corner maps to (0, 13.4) -> Wait, order in JSON was BL=[1607, 960] but dst order is TL, TR, BR, BL
    # dst_points: 
    # [0, 0] (TL)
    # [6.1, 0] (TR)
    # [6.1, 13.4] (BR)
    # [0, 13.4] (BL)
    
    # Let's check config vs class implementation:
    # Class src_points order: TL, TR, BR, BL
    # JSON BL is [1607, 960]
    # Class dst_points index 3 is [0, 13.4]
    # So [1607, 960] should map to [0, 13.4]
    
    cx, cy = transform.pixel_to_court(1607, 960)
    assert abs(cx - 0) < 0.1
    assert abs(cy - 13.4) < 0.1

def test_round_trip_conversion(court_config_file):
    transform = CourtTransform(court_config_file)
    px, py = 900, 600
    
    # Convert to court
    cx, cy = transform.pixel_to_court(px, py)
    
    # Convert back to pixel
    px2, py2 = transform.court_to_pixel(cx, cy)
    
    assert abs(px - px2) < 2
    assert abs(py - py2) < 2

def test_court_dimensions(court_config_file):
    transform = CourtTransform(court_config_file)
    width, length = transform.get_court_dimensions()
    assert width == 6.1
    assert length == 13.4
