from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import math
from collections import deque

class ActivityTracker:
    def __init__(self):
        self.current_session = None
        
        self.left_wrist_history = deque(maxlen=30)
        self.right_wrist_history = deque(maxlen=30)
        self.last_positions = {}
        self.last_timestamp = datetime.now()
        
        self.step_timestamps = []
        self.step_detection_cooldown = 0
        
        self.target_metrics = {
            "speed": 2.5,
            "stride_length": 0.7,
            "cadence": 160
        }
        
        self.running_metrics = []
        
        self.pixel_to_meter_ratio = 0.01

    def set_pixel_to_meter_ratio(self, frame_height):
        self.pixel_to_meter_ratio = 1.7 / frame_height
        
    def start_session(self) -> None:
        self.current_session = {
            "start_time": datetime.now(),
            "metrics": [],
            "total_distance": 0,
            "calories_burned": 0,
            "steps_count": 0,
            "max_speed": 0
        }
        
        self.left_wrist_history.clear()
        self.right_wrist_history.clear()
        self.last_positions = {}
        self.last_timestamp = datetime.now()
        self.step_timestamps = []
        self.running_metrics = []

    def end_session(self) -> Dict:
        if not self.current_session:
            return {}
            
        avg_metrics = self._calculate_average_metrics()
        
        session_data = {
            "duration": (datetime.now() - self.current_session["start_time"]).total_seconds(),
            "total_distance": self.current_session["total_distance"],
            "calories_burned": self.current_session["calories_burned"],
            "steps_count": self.current_session["steps_count"],
            "max_speed": self.current_session["max_speed"],
            "average_metrics": avg_metrics
        }
        
        self.current_session = None
        return session_data

    def update_metrics(self, hand_positions: Dict, frame_size) -> Dict:
        if not self.current_session or not hand_positions:
            return {}

        if frame_size and len(frame_size) >= 2:
            self.set_pixel_to_meter_ratio(frame_size[1])
            
        now = datetime.now()
        time_delta = (now - self.last_timestamp).total_seconds()
        self.last_timestamp = now
        
        if time_delta <= 0:
            return {}
        
        if 'left_wrist' in hand_positions:
            self.left_wrist_history.append(hand_positions['left_wrist'])
        if 'right_wrist' in hand_positions:
            self.right_wrist_history.append(hand_positions['right_wrist'])
        
        metrics = self._calculate_metrics_from_hands(time_delta)
        
        if metrics:
            self.running_metrics.append(metrics)
            self._update_session_stats(metrics, time_delta)
            
            return self._generate_feedback(metrics)
        
        return {}

    def _calculate_metrics_from_hands(self, time_delta: float) -> Dict[str, float]:
        if len(self.left_wrist_history) < 5 and len(self.right_wrist_history) < 5:
            return {}
        
        left_speed = self._calculate_hand_speed(self.left_wrist_history, time_delta)
        right_speed = self._calculate_hand_speed(self.right_wrist_history, time_delta)
        
        steps = self._detect_steps_from_hands()
        
        cadence = self._calculate_cadence()
        
        estimated_speed = self._estimate_running_speed(left_speed, right_speed, cadence)
        
        stride_length = self._estimate_stride_length(estimated_speed, cadence)
        
        metrics = {
            "speed": estimated_speed,
            "stride_length": stride_length,
            "cadence": cadence,
            "arm_movement": (left_speed + right_speed) / 2
        }
        
        return metrics

    def _calculate_hand_speed(self, history, time_delta: float) -> float:
        if len(history) < 2 or time_delta <= 0:
            return 0.0
        
        positions_to_use = min(5, len(history))
        
        if positions_to_use >= 2:
            current = history[-1]
            previous = history[-2]
            
            dx = current[0] - previous[0]
            dy = current[1] - previous[1]
            distance_pixels = math.sqrt(dx*dx + dy*dy)
            
            distance_meters = distance_pixels * self.pixel_to_meter_ratio
            
            immediate_speed = distance_meters / time_delta
            
            if positions_to_use > 2:
                total_distance = 0
                for i in range(1, positions_to_use):
                    p1 = history[-i]
                    p2 = history[-(i+1)]
                    dx = p1[0] - p2[0]
                    dy = p1[1] - p2[1]
                    total_distance += math.sqrt(dx*dx + dy*dy) * self.pixel_to_meter_ratio
                
                avg_speed = total_distance / (time_delta * (positions_to_use - 1))
                speed = immediate_speed * 0.7 + avg_speed * 0.3
            else:
                speed = immediate_speed
                
            speed *= 1.5
            
            return speed
        
        return 0.0

    def _detect_steps_from_hands(self) -> int:
        steps = 0
        
        if len(self.right_wrist_history) < 5 and len(self.left_wrist_history) < 5:
            return steps
            
        if self.step_detection_cooldown <= 0:
            detected = False
            
            if len(self.right_wrist_history) >= 5:
                y_vals = [pos[1] for pos in list(self.right_wrist_history)[-5:]]
                
                moves_up = sum(1 for i in range(len(y_vals)-1) if y_vals[i] > y_vals[i+1])
                moves_down = sum(1 for i in range(len(y_vals)-1) if y_vals[i] < y_vals[i+1])
                
                if len(y_vals) >= 3:
                    if (y_vals[1] > y_vals[0] and 
                        y_vals[2] > y_vals[1] and 
                        abs(y_vals[2] - y_vals[0]) > 5):
                        detected = True
                    
                    elif (y_vals[1] < y_vals[0] and 
                          y_vals[2] < y_vals[1] and 
                          abs(y_vals[2] - y_vals[0]) > 5):
                        detected = True
                    
            if not detected and len(self.left_wrist_history) >= 5:
                y_vals = [pos[1] for pos in list(self.left_wrist_history)[-5:]]
                
                if len(y_vals) >= 3:
                    if (y_vals[1] > y_vals[0] and 
                        y_vals[2] > y_vals[1] and 
                        abs(y_vals[2] - y_vals[0]) > 5):
                        detected = True
                    elif (y_vals[1] < y_vals[0] and 
                          y_vals[2] < y_vals[1] and 
                          abs(y_vals[2] - y_vals[0]) > 5):
                        detected = True
            
            if detected:
                self.step_timestamps.append(datetime.now())
                
                self.current_session["steps_count"] += 1
                
                self.step_detection_cooldown = 8
                
                steps = 1
                print(f"Step detected! Total: {self.current_session['steps_count']}")
        else:
            self.step_detection_cooldown -= 1
            
        return steps

    def _calculate_cadence(self) -> float:
        cutoff_time = datetime.now() - timedelta(seconds=10)
        self.step_timestamps = [ts for ts in self.step_timestamps if ts > cutoff_time]
        
        if len(self.step_timestamps) < 4:
            return 0.0
            
        time_span = (self.step_timestamps[-1] - self.step_timestamps[0]).total_seconds()
        if time_span <= 0:
            return 0.0
            
        steps_count = len(self.step_timestamps)
        steps_per_second = steps_count / time_span
        steps_per_minute = steps_per_second * 60
        
        return steps_per_minute

    def _estimate_running_speed(self, left_speed: float, right_speed: float, cadence: float) -> float:
        arm_speed = max(left_speed, right_speed)
        
        arm_speed *= 2.5
        
        if cadence > 0:
            estimated_speed = arm_speed * 0.7 + (cadence / 160.0) * 2.0
        else:
            estimated_speed = arm_speed
            
        if estimated_speed < 0.5 and (left_speed > 0.1 or right_speed > 0.1):
            estimated_speed = 1.0
            
        estimated_speed = max(0.0, min(6.0, estimated_speed))
        
        print(f"Arm speeds: L={left_speed:.2f}, R={right_speed:.2f}, Final speed={estimated_speed:.2f}")
        
        return estimated_speed

    def _estimate_stride_length(self, speed: float, cadence: float) -> float:
        if cadence <= 0:
            return self.target_metrics["stride_length"]
            
        stride_length = (speed * 60) / cadence * 2
        
        stride_length = max(0.4, min(2.0, stride_length))
        
        return stride_length

    def _update_session_stats(self, metrics: Dict[str, float], time_delta: float) -> None:
        speed = metrics.get("speed", 0)
        
        distance_increment = speed * time_delta
        self.current_session["total_distance"] += distance_increment
        
        self.current_session["max_speed"] = max(self.current_session["max_speed"], speed)
        
        self.current_session["calories_burned"] += self._calculate_calories(speed, time_delta)

    def _calculate_average_metrics(self) -> Dict[str, float]:
        if not self.running_metrics:
            return {}
            
        speeds = [m.get("speed", 0) for m in self.running_metrics]
        strides = [m.get("stride_length", 0) for m in self.running_metrics]
        cadences = [m.get("cadence", 0) for m in self.running_metrics if m.get("cadence", 0) > 0]
        
        avg_metrics = {
            "avg_speed": np.mean(speeds) if speeds else 0,
            "avg_stride_length": np.mean(strides) if strides else 0,
            "avg_cadence": np.mean(cadences) if cadences else 0
        }
        
        return avg_metrics

    def _calculate_calories(self, speed: float, time_delta: float) -> float:
        if speed < 1.5:
            met = 2.5
        elif speed < 2.5:
            met = 7.0
        elif speed < 4.0:
            met = 10.0
        else:
            met = 12.5
            
        return (met * 3.5 * 70) / (200 * 60) * time_delta

    def _generate_feedback(self, metrics: Dict[str, float]) -> Dict[str, str]:
        feedback = {}
        
        speed = metrics.get("speed", 0)
        cadence = metrics.get("cadence", 0)
        stride_length = metrics.get("stride_length", 0)
        
        if speed < 1.5:
            feedback["speed"] = "Walking pace detected"
        elif speed < self.target_metrics["speed"] * 0.8:
            feedback["speed"] = "Try to increase your pace"
        elif speed > self.target_metrics["speed"] * 1.5:
            feedback["speed"] = "Great pace! Maintain it if comfortable"
            
        if cadence > 0:
            if cadence < self.target_metrics["cadence"] * 0.8:
                feedback["cadence"] = "Try taking quicker steps"
            elif cadence > 190:
                feedback["cadence"] = "Consider slightly longer strides with fewer steps"
                
        if stride_length > 0 and stride_length < self.target_metrics["stride_length"] * 0.8:
            feedback["stride"] = "Try to lengthen your stride slightly"
            
        return feedback