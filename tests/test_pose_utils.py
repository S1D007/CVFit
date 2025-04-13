import pytest
import numpy as np
from utils.pose_utils import PoseUtils

def test_calculate_angle():
    """Test the angle calculation function."""
    # Create three points forming a right angle
    p1 = np.array([0, 0])
    p2 = np.array([0, 1])
    p3 = np.array([1, 1])

    angle = PoseUtils.calculate_angle(p1, p2, p3)
    assert abs(angle - 90.0) < 0.01  # Should be close to 90 degrees

def test_calculate_stability_score():
    """Test stability score calculation."""
    # Create stable position history (low variance)
    stable_positions = [np.array([100, 100]) for _ in range(15)]
    stability = PoseUtils.calculate_stability_score(stable_positions)
    assert stability > 0.8  # Stable positions should have high stability

    # Create unstable position history (high variance)
    unstable_positions = [np.array([100 + i*10, 100 + i*8]) for i in range(15)]
    unstable_stability = PoseUtils.calculate_stability_score(unstable_positions)
    assert unstable_stability < stability  # Should be less stable
