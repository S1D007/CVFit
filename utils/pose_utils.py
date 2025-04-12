import numpy as np
from typing import Dict, List, Tuple, Optional

class PoseUtils:
    @staticmethod
    def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        v1 = p1 - p2
        v2 = p3 - p2
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

    @staticmethod
    def calculate_velocity(positions: List[np.ndarray], time_delta: float) -> np.ndarray:
        if len(positions) < 2:
            return np.zeros(3)
        return (positions[-1] - positions[-2]) / time_delta

    @staticmethod
    def smoothen_keypoints(keypoints: List[Dict], window_size: int = 5) -> Dict:
        if len(keypoints) < window_size:
            return keypoints[-1] if keypoints else {}

        smoothed = {}
        for key in keypoints[0].keys():
            points = np.array([kp[key] for kp in keypoints[-window_size:]])
            smoothed[key] = np.mean(points, axis=0)
        return smoothed

    @staticmethod
    def detect_movement_type(keypoints: Dict) -> str:
        if not keypoints:
            return "unknown"

        knee_angle = PoseUtils.calculate_angle(
            keypoints["hips"][0],
            keypoints["knees"][0],
            keypoints["ankles"][0]
        )

        if knee_angle < 150:
            return "running"
        return "walking"

    @staticmethod
    def calculate_stability_score(positions: List[np.ndarray]) -> float:
        if len(positions) < 10:
            return 1.0
            
        vertical_movement = np.std([p[1] for p in positions])
        lateral_movement = np.std([p[0] for p in positions])
        
        stability = 1.0 - min(1.0, (vertical_movement + lateral_movement) / 0.2)
        return max(0.0, stability)