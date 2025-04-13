import cv2
import numpy as np
import os
import tempfile
import pathlib
from ultralytics import YOLO
import supervision as sv
from typing import Optional, Dict, List, Tuple

def setup_temp_dir():
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    os.environ['TMPDIR'] = temp_dir
    os.environ['TEMP'] = temp_dir
    os.environ['TMP'] = temp_dir
    tempfile.tempdir = temp_dir
    return temp_dir

class PoseEngine:
    def __init__(self):
        self.temp_dir = setup_temp_dir()

        self.model = YOLO('yolov8n-pose.pt')

        self.box_annotator = sv.BoxAnnotator(
            color=sv.ColorPalette.DEFAULT,
            thickness=2
        )
        self.keypoint_names = {
            0: "nose", 1: "left_eye", 2: "right_eye", 3: "left_ear", 4: "right_ear",
            5: "left_shoulder", 6: "right_shoulder", 7: "left_elbow", 8: "right_elbow",
            9: "left_wrist", 10: "right_wrist", 11: "left_hip", 12: "right_hip",
            13: "left_knee", 14: "right_knee", 15: "left_ankle", 16: "right_ankle"
        }
        self.skeleton = [
            [5, 7], [7, 9],  # left arm
            [6, 8], [8, 10],  # right arm
            [5, 11], [6, 12],  # shoulders to hips
            [11, 13], [13, 15],  # left leg
            [12, 14], [14, 16],  # right leg
            [11, 12],  # hips
            [5, 6]  # shoulders
        ]
        self.color_map = {
            "arms": (0, 255, 0),     # green
            "legs": (255, 0, 0),     # blue
            "torso": (0, 165, 255),  # orange
            "face": (255, 0, 255)    # magenta
        }
        self.confidence_threshold = 0.5

    def process_frame(self, frame: np.ndarray):
        """
        Process a frame with pose detection.

        Args:
            frame: The input video frame

        Returns:
            tuple: (processed_frame, keypoint_positions)
                - processed_frame: The annotated frame with full body tracking visualization
                - keypoint_positions: Dictionary of detected keypoint positions for metrics
        """
        if frame is None:
            return None, {}

        display_frame = frame.copy()

        results = self.model(frame)[0]

        keypoints = results.keypoints

        keypoint_positions = {}

        if keypoints is not None and len(keypoints) > 0:
            kpt_data = keypoints.data.cpu().numpy()
            best_person_idx = 0
            if len(kpt_data) > 1:
                avg_confidences = [np.mean([k[2] for k in person if k[2] > 0]) for person in kpt_data]
                best_person_idx = np.argmax(avg_confidences)

            kpts = kpt_data[best_person_idx]
            for idx, kpt in enumerate(kpts):
                if kpt[2] > self.confidence_threshold:
                    keypoint_name = self.keypoint_names.get(idx, f"kpt_{idx}")
                    keypoint_positions[keypoint_name] = (float(kpt[0]), float(kpt[1]))
            for p1_idx, p2_idx in self.skeleton:
                if (p1_idx < len(kpts) and p2_idx < len(kpts) and
                    kpts[p1_idx][2] > self.confidence_threshold and kpts[p2_idx][2] > self.confidence_threshold):

                    x1, y1 = int(kpts[p1_idx][0]), int(kpts[p1_idx][1])
                    x2, y2 = int(kpts[p2_idx][0]), int(kpts[p2_idx][1])
                    if p1_idx in [5, 6, 7, 8, 9, 10] and p2_idx in [5, 6, 7, 8, 9, 10]:
                        color = self.color_map["arms"]
                    elif p1_idx in [11, 12, 13, 14, 15, 16] and p2_idx in [11, 12, 13, 14, 15, 16]:
                        color = self.color_map["legs"]
                    else:
                        color = self.color_map["torso"]

                    cv2.line(display_frame, (x1, y1), (x2, y2), color, 2)
            for idx, kpt in enumerate(kpts):
                if kpt[2] > self.confidence_threshold:
                    x, y = int(kpt[0]), int(kpt[1])
                    if idx in [0, 1, 2, 3, 4]:
                        color = self.color_map["face"]
                    elif idx in [5, 6, 7, 8, 9, 10]:
                        color = self.color_map["arms"]
                    else:
                        color = self.color_map["legs"]

                    cv2.circle(display_frame, (x, y), 6, color, -1)
                    if idx in [9, 10, 15, 16]:
                        label = "L" if idx in [9, 15] else "R"
                        cv2.putText(display_frame, label, (x+5, y+5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        if keypoint_positions:
            cv2.putText(display_frame, "Full body tracking active", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return display_frame, keypoint_positions
