import cv2
import numpy as np
import json


class CourtTransform:
    """
    Handles perspective transformation from video pixel coordinates to real-world court coordinates (meters).
    """
    
    COURT_WIDTH_M = 6.1   # 20 feet
    COURT_LENGTH_M = 13.4  # 44 feet

    def __init__(self, court_config_path: str):
        """
        Initialize the court transformer.

        Args:
            court_config_path (str): Path to the JSON configuration file containing court corner points.
        """
        with open(court_config_path) as f:
            config = json.load(f)
        
        # Source points from video (pixel coordinates)
        corners = config["court_corners"]
        self.src_points = np.float32([
            corners["top_left"],
            corners["top_right"],
            corners["bottom_right"],
            corners["bottom_left"],
        ])
        
        # Destination points (court coordinates in meters)
        # Order must match src_points: top-left, top-right, bottom-right, bottom-left
        self.dst_points = np.float32([
            [0, 0],
            [self.COURT_WIDTH_M, 0],
            [self.COURT_WIDTH_M, self.COURT_LENGTH_M],
            [0, self.COURT_LENGTH_M],
        ])
        
        # Compute transform matrices
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)
        self.M_inv = cv2.getPerspectiveTransform(self.dst_points, self.src_points)
    
    def pixel_to_court(self, x: int, y: int) -> tuple[float, float]:
        """
        Convert pixel coordinates to court coordinates in meters.

        Args:
            x (int): X-coordinate in pixels.
            y (int): Y-coordinate in pixels.

        Returns:
            tuple[float, float]: (x, y) coordinates in meters relative to the court origin (top-left).
        """
        point = np.float32([[x, y]]).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.M)
        return float(transformed[0][0][0]), float(transformed[0][0][1])
    
    def court_to_pixel(self, x: float, y: float) -> tuple[int, int]:
        """
        Convert court coordinates (meters) back to pixel coordinates.

        Args:
            x (float): X-coordinate in meters.
            y (float): Y-coordinate in meters.

        Returns:
            tuple[int, int]: (x, y) coordinates in pixels.
        """
        point = np.float32([[x, y]]).reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(point, self.M_inv)
        return int(transformed[0][0][0]), int(transformed[0][0][1])

    def get_court_dimensions(self) -> tuple[float, float]:
        """
        Get the standard dimensions of the pickleball court.

        Returns:
            tuple[float, float]: (width, length) in meters.
        """
        return self.COURT_WIDTH_M, self.COURT_LENGTH_M
