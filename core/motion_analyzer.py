import numpy as np
from typing import Dict, List, Tuple
from scipy.signal import find_peaks

class MotionAnalyzer:
    def __init__(self):
        self.motion_buffer = []
        self.buffer_size = 90
        self.peak_threshold = 0.15

    def analyze_motion(self, keypoints: Dict) -> Dict[str, float]:
        if not keypoints:
            return {"movement_quality": 0.0, "symmetry_score": 0.0}

        hip_positions = np.array(keypoints["hips"])
        knee_positions = np.array(keypoints["knees"])
        
        movement_quality = self._calculate_movement_quality(hip_positions, knee_positions)
        symmetry_score = self._calculate_symmetry(hip_positions, knee_positions)
        
        return {
            "movement_quality": movement_quality,
            "symmetry_score": symmetry_score
        }

    def _calculate_movement_quality(self, hips: np.ndarray, knees: np.ndarray) -> float:
        knee_angles = self._calculate_joint_angles(hips, knees)
        hip_stability = 1.0 - np.std(hips[:, 1]) / 0.1
        return min(1.0, max(0.0, (knee_angles.mean() + hip_stability) / 2))

    def _calculate_symmetry(self, hips: np.ndarray, knees: np.ndarray) -> float:
        left_side = np.linalg.norm(hips[0] - knees[0])
        right_side = np.linalg.norm(hips[1] - knees[1])
        symmetry = 1.0 - abs(left_side - right_side) / max(left_side, right_side)
        return min(1.0, max(0.0, symmetry))

    def _calculate_joint_angles(self, point1: np.ndarray, point2: np.ndarray) -> np.ndarray:
        vectors = point2 - point1
        angles = np.arctan2(vectors[:, 1], vectors[:, 0])
        return np.abs(angles)

    def detect_repetitions(self, vertical_positions: List[float]) -> int:
        if len(vertical_positions) < self.buffer_size:
            return 0
            
        peaks, _ = find_peaks(vertical_positions, height=self.peak_threshold, distance=15)
        return len(peaks)