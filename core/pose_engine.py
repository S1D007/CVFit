import cv2
import numpy as np
import os
import tempfile
import pathlib
from ultralytics import YOLO
import supervision as sv
from typing import Optional

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
        
        self.hand_keypoints = [5, 6, 7, 8, 9, 10]
        
    def process_frame(self, frame: np.ndarray):
        """
        Process a frame with pose detection.
        
        Args:
            frame: The input video frame
            
        Returns:
            tuple: (processed_frame, hand_positions)
                - processed_frame: The annotated frame with hand tracking visualization
                - hand_positions: Dictionary of detected hand positions for metrics
        """
        if frame is None:
            return None, {}

        display_frame = frame.copy()
        
        results = self.model(frame)[0]
        
        keypoints = results.keypoints
        
        hand_positions = {}
        
        if keypoints is not None and len(keypoints) > 0:
            kpt_data = keypoints.data.cpu().numpy()
            for kpts in kpt_data:
                if len(kpts) > max(self.hand_keypoints):
                    if kpts[9][2] > 0.5:
                        hand_positions['left_wrist'] = (float(kpts[9][0]), float(kpts[9][1]))
                    if kpts[10][2] > 0.5:
                        hand_positions['right_wrist'] = (float(kpts[10][0]), float(kpts[10][1]))
                
                for idx in self.hand_keypoints:
                    if idx < len(kpts) and kpts[idx][2] > 0.5:
                        x, y = int(kpts[idx][0]), int(kpts[idx][1])
                        cv2.circle(display_frame, (x, y), 6, (0, 255, 0), -1)
                        if idx == 9:
                            cv2.putText(display_frame, "L", (x+5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        elif idx == 10:
                            cv2.putText(display_frame, "R", (x+5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                arm_skeleton = [[5, 7], [7, 9], [6, 8], [8, 10]]
                
                for p1, p2 in arm_skeleton:
                    if (p1 < len(kpts) and p2 < len(kpts) and 
                        kpts[p1][2] > 0.5 and kpts[p2][2] > 0.5):
                        x1, y1 = int(kpts[p1][0]), int(kpts[p1][1])
                        x2, y2 = int(kpts[p2][0]), int(kpts[p2][1])
                        cv2.line(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        if hand_positions:
            cv2.putText(display_frame, "Hand tracking active", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
        return display_frame, hand_positions