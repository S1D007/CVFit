import cv2
import numpy as np
from typing import Tuple, Optional
import threading
import queue
import time

class VideoCapture:
    def __init__(self, source: int = 0):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.frame_queue = queue.Queue(maxsize=2)
        self.stopped = False
        self.frame_dimensions = (640, 480)
        self.error = None
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_dimensions[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_dimensions[1])
        
    def start(self):
        self.error = None
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened() and self.source == 0:
                for alt_source in [1, 2, -1]:
                    self.cap = cv2.VideoCapture(alt_source)
                    if self.cap.isOpened():
                        self.source = alt_source
                        break
        
        if self.cap.isOpened():
            threading.Thread(target=self._update, daemon=True).start()
        else:
            self.error = "Could not access any camera"
            
        return self

    def _update(self):
        consecutive_failures = 0
        
        while not self.stopped:
            if not self.frame_queue.full():
                ret, frame = self.cap.read()
                if ret:
                    consecutive_failures = 0
                    frame = cv2.resize(frame, self.frame_dimensions)
                    self.frame_queue.put(frame)
                else:
                    consecutive_failures += 1
                    if consecutive_failures > 10:
                        self.error = "Camera disconnected or not providing frames"
                        break
            
            time.sleep(0.01)

    def read(self) -> Optional[np.ndarray]:
        try:
            if not self.frame_queue.empty():
                return self.frame_queue.get(block=False)
            return None
        except:
            return None

    def release(self):
        self.stopped = True
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()

    def get_frame_dimensions(self) -> Tuple[int, int]:
        return self.frame_dimensions
    
    def set_frame_dimensions(self, width: int, height: int):
        self.frame_dimensions = (width, height)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def is_opened(self) -> bool:
        return self.cap.isOpened() and self.error is None
        
    def get_error(self) -> Optional[str]:
        return self.error