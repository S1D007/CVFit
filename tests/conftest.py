import os
import sys
import pytest
import numpy as np

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_frame():
    """Create a sample video frame for testing."""
    # Create a 720x1280 frame (standard HD resolution)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame.fill(200)  # Light gray background

    return frame

@pytest.fixture
def mock_keypoints():
    """Return mock pose keypoints for testing."""
    return {
        'left_wrist': (640, 400),
        'right_wrist': (680, 420)
    }
