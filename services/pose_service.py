from fastapi import FastAPI, WebSocket
from typing import Dict, Optional
import asyncio
import json

from ..core.pose_engine import PoseEngine
from ..core.motion_analyzer import MotionAnalyzer
from ..core.activity_tracker import ActivityTracker
from ..utils.video_capture import VideoCapture
from ..utils.pose_utils import PoseUtils

class PoseService:
    def __init__(self):
        self.pose_engine = PoseEngine()
        self.motion_analyzer = MotionAnalyzer()
        self.activity_tracker = ActivityTracker()
        self.video_capture = None
        self.active_connections = set()
        self.processing = False

    async def start_tracking(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if not self.video_capture:
            self.video_capture = VideoCapture().start()
            self.activity_tracker.start_session()
            self.processing = True
            
        try:
            await self._process_frames(websocket)
        finally:
            self.active_connections.remove(websocket)
            if not self.active_connections:
                self._cleanup()

    async def _process_frames(self, websocket: WebSocket):
        last_time = asyncio.get_event_loop().time()
        
        while self.processing and self.video_capture.is_opened():
            frame = self.video_capture.read()
            if frame is None:
                continue

            current_time = asyncio.get_event_loop().time()
            time_delta = current_time - last_time
            last_time = current_time

            landmarks = self.pose_engine.process_frame(frame)
            if landmarks is not None:
                keypoints = self.pose_engine.extract_keypoints(landmarks)
                motion_data = self.motion_analyzer.analyze_motion(keypoints)
                metrics = self.activity_tracker.update_metrics(motion_data, time_delta)

                await websocket.send_json({
                    "metrics": metrics,
                    "movement_type": PoseUtils.detect_movement_type(keypoints),
                    "stability": PoseUtils.calculate_stability_score(landmarks)
                })

            await asyncio.sleep(0.033)  # ~30 FPS

    def _cleanup(self):
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.processing = False
        session_data = self.activity_tracker.end_session()
        return session_data