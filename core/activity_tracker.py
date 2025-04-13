from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import math
from collections import deque
from models.user import UserProfile

class ActivityTracker:
    def __init__(self):
        self.current_session = None
        self.keypoints_history = {
            "left_wrist": deque(maxlen=30),
            "right_wrist": deque(maxlen=30),
            "left_ankle": deque(maxlen=30),
            "right_ankle": deque(maxlen=30),
            "left_knee": deque(maxlen=30),
            "right_knee": deque(maxlen=30),
            "left_hip": deque(maxlen=30),
            "right_hip": deque(maxlen=30)
        }

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
        self.user_profile = UserProfile()
        self.vertical_oscillation_buffer = deque(maxlen=60)

    def set_user_profile(self, profile: UserProfile):
        """Set user profile for personalized metrics"""
        self.user_profile = profile
        self.target_metrics["stride_length"] = profile.get_stride_length()

    def set_pixel_to_meter_ratio(self, frame_height):
        """Calibrate pixel to meter conversion based on frame height and user height"""
        person_height_pixels = frame_height * 0.9
        person_height_meters = self.user_profile.height / 100.0  # convert cm to meters
        self.pixel_to_meter_ratio = person_height_meters / person_height_pixels

    def start_session(self) -> None:
        self.current_session = {
            "start_time": datetime.now(),
            "metrics": [],
            "total_distance": 0,
            "calories_burned": 0,
            "steps_count": 0,
            "max_speed": 0
        }
        for key in self.keypoints_history:
            self.keypoints_history[key].clear()

        self.last_positions = {}
        self.last_timestamp = datetime.now()
        self.step_timestamps = []
        self.running_metrics = []
        self.vertical_oscillation_buffer.clear()

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

    def update_metrics(self, keypoint_positions: Dict, frame_size) -> Dict:
        """
        Update metrics based on detected keypoints.
        Only calculates metrics when a valid person is detected in frame.
        """
        if not self.current_session:
            return {}
        if not keypoint_positions:
            return {"status": "No person detected"}
        required_parts = [
            ["left_ankle", "right_ankle"],  # Best case: both ankles visible
            ["left_knee", "right_knee"],    # Second best: knees visible
            ["left_wrist", "right_wrist"]   # Fallback: at least wrists visible
        ]

        has_required_parts = False
        for part_group in required_parts:
            if any(part in keypoint_positions for part in part_group):
                has_required_parts = True
                break

        if not has_required_parts:
            return {"status": "Person detected but key body parts not visible"}
        if sum(1 for part in keypoint_positions if part in self.keypoints_history) < 2:
            return {"status": "Insufficient keypoints for tracking"}

        if frame_size and len(frame_size) >= 2:
            self.set_pixel_to_meter_ratio(frame_size[1])

        now = datetime.now()
        time_delta = (now - self.last_timestamp).total_seconds()
        self.last_timestamp = now

        if time_delta <= 0 or time_delta > 1.0:  # Skip if time delta is invalid or too large
            return {"status": "Calibrating timing..."}
        for key, position in keypoint_positions.items():
            if key in self.keypoints_history:
                self.keypoints_history[key].append(position)
        metrics = self._calculate_full_body_metrics(time_delta)

        if metrics and metrics.get("speed", 0) > 0:
            self.running_metrics.append(metrics)
            self._update_session_stats(metrics, time_delta)

            return self._generate_feedback(metrics)

        return {"status": "Standing still"}

    def _calculate_full_body_metrics(self, time_delta: float) -> Dict[str, float]:
        """Calculate metrics using full body keypoints"""
        required_points = ["left_ankle", "right_ankle"]
        if not all(len(self.keypoints_history.get(point, [])) >= 3 for point in required_points):
            if len(self.keypoints_history["left_wrist"]) >= 3 or len(self.keypoints_history["right_wrist"]) >= 3:
                return self._calculate_metrics_from_arms(time_delta)
            return {}
        steps = self._detect_steps_from_ankles()
        if steps == 0 and (len(self.keypoints_history["left_knee"]) >= 3 or len(self.keypoints_history["right_knee"]) >= 3):
            steps = self._detect_steps_from_knees()
        if steps == 0 and (len(self.keypoints_history["left_wrist"]) >= 3 or len(self.keypoints_history["right_wrist"]) >= 3):
            steps = self._detect_steps_from_arms()

        cadence = self._calculate_cadence()
        vertical_oscillation = self._calculate_vertical_oscillation()
        ankle_speed = self._calculate_leg_speed(time_delta)
        arm_speed = self._calculate_arm_speed(time_delta)
        estimated_speed = self._estimate_running_speed(arm_speed, ankle_speed, cadence)
        stride_length = self._estimate_stride_length(estimated_speed, cadence)

        metrics = {
            "speed": estimated_speed,
            "stride_length": stride_length,
            "cadence": cadence,
            "vertical_oscillation": vertical_oscillation,
            "arm_movement": arm_speed,
            "leg_movement": ankle_speed
        }

        return metrics

    def _calculate_metrics_from_arms(self, time_delta: float) -> Dict[str, float]:
        """Legacy method for arm-only metrics calculation"""
        left_speed = self._calculate_keypoint_speed(self.keypoints_history["left_wrist"], time_delta)
        right_speed = self._calculate_keypoint_speed(self.keypoints_history["right_wrist"], time_delta)

        steps = self._detect_steps_from_arms()
        cadence = self._calculate_cadence()
        arm_speed = max(left_speed, right_speed)
        estimated_speed = arm_speed * 2.5

        if cadence > 0:
            estimated_speed = arm_speed * 0.7 + (cadence / 160.0) * 2.0

        estimated_speed = max(0.0, min(6.0, estimated_speed))

        stride_length = self._estimate_stride_length(estimated_speed, cadence)

        return {
            "speed": estimated_speed,
            "stride_length": stride_length,
            "cadence": cadence,
            "arm_movement": arm_speed,
            "leg_movement": 0.0
        }

    def _calculate_arm_speed(self, time_delta: float) -> float:
        """Calculate speed based on arm movements"""
        left_speed = self._calculate_keypoint_speed(self.keypoints_history["left_wrist"], time_delta)
        right_speed = self._calculate_keypoint_speed(self.keypoints_history["right_wrist"], time_delta)
        return max(left_speed, right_speed) * 0.8

    def _calculate_leg_speed(self, time_delta: float) -> float:
        """Calculate speed based on leg movements"""
        left_speed = self._calculate_keypoint_speed(self.keypoints_history["left_ankle"], time_delta)
        right_speed = self._calculate_keypoint_speed(self.keypoints_history["right_ankle"], time_delta)
        return max(left_speed, right_speed) * 1.2

    def _calculate_keypoint_speed(self, history, time_delta: float) -> float:
        """Calculate speed of any keypoint based on its movement history"""
        if len(history) < 2 or time_delta <= 0:
            return 0.0

        positions_to_use = min(5, len(history))

        if positions_to_use >= 2:
            current = history[-1]
            previous = history[-2]

            dx = current[0] - previous[0]
            dy = current[1] - previous[1]
            if abs(dx) < 2.0 and abs(dy) < 2.0:
                return 0.0

            distance_pixels = math.sqrt(dx*dx + dy*dy)
            if distance_pixels > 100:
                return 0.0

            distance_meters = distance_pixels * self.pixel_to_meter_ratio
            immediate_speed = distance_meters / time_delta
            immediate_speed = min(8.0, immediate_speed)

            if positions_to_use > 2:
                valid_movements = 0
                total_distance = 0

                for i in range(1, positions_to_use):
                    p1 = history[-i]
                    p2 = history[-(i+1)]
                    dx = p1[0] - p2[0]
                    dy = p1[1] - p2[1]
                    if abs(dx) < 2.0 and abs(dy) < 2.0:
                        continue

                    movement = math.sqrt(dx*dx + dy*dy)
                    if movement > 100:
                        continue

                    total_distance += movement * self.pixel_to_meter_ratio
                    valid_movements += 1

                if valid_movements > 0:
                    avg_speed = total_distance / (time_delta * valid_movements)
                    speed = immediate_speed * 0.3 + avg_speed * 0.7
                else:
                    speed = immediate_speed
            else:
                speed = immediate_speed
            return min(6.0, max(0.0, speed))

        return 0.0

    def _detect_steps_from_ankles(self) -> int:
        """Detect steps by analyzing ankle vertical movement patterns"""
        steps = 0

        if self.step_detection_cooldown <= 0:
            if len(self.keypoints_history["left_ankle"]) >= 5 or len(self.keypoints_history["right_ankle"]) >= 5:
                left_detected = self._detect_step_pattern(self.keypoints_history["left_ankle"])
                right_detected = self._detect_step_pattern(self.keypoints_history["right_ankle"])

                if left_detected or right_detected:
                    self.step_timestamps.append(datetime.now())
                    self.current_session["steps_count"] += 1
                    self.step_detection_cooldown = 10  # Higher cooldown for more accurate counts
                    steps = 1
                    print(f"Step detected from ankle! Total: {self.current_session['steps_count']}")
        else:
            self.step_detection_cooldown -= 1

        return steps

    def _detect_steps_from_knees(self) -> int:
        """Backup step detection using knee movement"""
        steps = 0

        if self.step_detection_cooldown <= 0:
            if len(self.keypoints_history["left_knee"]) >= 5 or len(self.keypoints_history["right_knee"]) >= 5:
                left_detected = self._detect_step_pattern(self.keypoints_history["left_knee"])
                right_detected = self._detect_step_pattern(self.keypoints_history["right_knee"])

                if left_detected or right_detected:
                    self.step_timestamps.append(datetime.now())
                    self.current_session["steps_count"] += 1
                    self.step_detection_cooldown = 9
                    steps = 1
                    print(f"Step detected from knee! Total: {self.current_session['steps_count']}")
        else:
            self.step_detection_cooldown -= 1

        return steps

    def _detect_steps_from_arms(self) -> int:
        """Legacy step detection from arm movements as fallback"""
        steps = 0

        if self.step_detection_cooldown <= 0:
            left_detected = self._detect_step_pattern(self.keypoints_history["left_wrist"])
            right_detected = self._detect_step_pattern(self.keypoints_history["right_wrist"])

            if left_detected or right_detected:
                self.step_timestamps.append(datetime.now())
                self.current_session["steps_count"] += 1
                self.step_detection_cooldown = 8
                steps = 1
                print(f"Step detected from arm! Total: {self.current_session['steps_count']}")
        else:
            self.step_detection_cooldown -= 1

        return steps

    def _detect_step_pattern(self, history) -> bool:
        """Generic pattern detection for steps from any keypoint's vertical movement"""
        if len(history) < 5:
            return False
        y_vals = [pos[1] for pos in list(history)[-5:]]
        pattern_1 = (y_vals[1] > y_vals[0] and
                    y_vals[2] > y_vals[1] and
                    abs(y_vals[2] - y_vals[0]) > 5)
        pattern_2 = (y_vals[1] < y_vals[0] and
                    y_vals[2] < y_vals[1] and
                    abs(y_vals[2] - y_vals[0]) > 5)
        direction_changes = sum(1 for i in range(len(y_vals)-2)
                              if (y_vals[i] < y_vals[i+1] and y_vals[i+1] > y_vals[i+2]) or
                                 (y_vals[i] > y_vals[i+1] and y_vals[i+1] < y_vals[i+2]))
        detected = pattern_1 or pattern_2 or direction_changes >= 2

        return detected

    def _calculate_cadence(self) -> float:
        """Calculate cadence (steps per minute) from recent step timestamps"""
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

    def _calculate_vertical_oscillation(self) -> float:
        """Calculate vertical oscillation using hip position variance"""
        if len(self.keypoints_history["left_hip"]) > 5 and len(self.keypoints_history["right_hip"]) > 5:
            left_y = [pos[1] for pos in list(self.keypoints_history["left_hip"])[-10:]]
            right_y = [pos[1] for pos in list(self.keypoints_history["right_hip"])[-10:]]
            avg_y = [(left_y[i] + right_y[i])/2 for i in range(min(len(left_y), len(right_y)))]

            if avg_y:
                oscillation = np.std(avg_y) * self.pixel_to_meter_ratio
                self.vertical_oscillation_buffer.append(oscillation)
                return oscillation
        if len(self.vertical_oscillation_buffer) > 0:
            return np.mean(self.vertical_oscillation_buffer)
        return 0.05  # Default value in meters

    def _estimate_running_speed(self, arm_speed: float, leg_speed: float, cadence: float) -> float:
        """Improved running speed estimation using both arm and leg movement with reality checks"""
        if arm_speed < 0.1 and leg_speed < 0.1:
            return 0.0  # No significant movement detected
        if leg_speed > 0:
            speed = leg_speed * 0.6 + arm_speed * 0.2
        else:
            speed = arm_speed * 0.5
        if cadence > 0:
            if cadence < 200:  # Apply realistic cadence cap
                cadence_factor = cadence / 160.0  # Normalize to typical running cadence
                speed = speed * 0.7 + (cadence_factor * speed) * 0.3
        if speed < 0.1:
            return 0.0
        elif speed < 0.5 and (arm_speed > 0.05 or leg_speed > 0.05):
            return max(0.5, min(1.2, speed * 2))
        elif speed > 4.0:
            return min(4.0, speed * 0.7)
        return max(0.0, min(5.0, speed))

    def _estimate_stride_length(self, speed: float, cadence: float) -> float:
        """Estimate stride length based on speed, cadence and user height"""
        if cadence <= 0:
            return self.user_profile.get_stride_length()
        stride_length = (speed * 60) / (cadence * 0.5)
        min_stride = self.user_profile.height * 0.003  # Minimum stride ~0.3% of height
        max_stride = self.user_profile.height * 0.013  # Maximum stride ~1.3% of height

        stride_length = max(min_stride, min(max_stride, stride_length))

        return stride_length

    def _update_session_stats(self, metrics: Dict[str, float], time_delta: float) -> None:
        """Update session statistics based on latest metrics with validation"""
        speed = metrics.get("speed", 0)
        if speed > 0.1:
            distance_increment = speed * time_delta
            if distance_increment <= 10.0:
                self.current_session["total_distance"] += distance_increment
                if speed < 10.0:  # Sanity check on max speed
                    self.current_session["max_speed"] = max(self.current_session["max_speed"], speed)
                calories = self._calculate_calories(speed, time_delta)
                self.current_session["calories_burned"] += calories

    def _calculate_average_metrics(self) -> Dict[str, float]:
        """Calculate average metrics across the session"""
        if not self.running_metrics:
            return {}

        metrics_keys = ["speed", "stride_length", "cadence", "vertical_oscillation"]
        avg_metrics = {}

        for key in metrics_keys:
            values = [m.get(key, 0) for m in self.running_metrics if key in m]
            if values:
                avg_metrics[f"avg_{key}"] = np.mean(values)
            else:
                avg_metrics[f"avg_{key}"] = 0

        return avg_metrics

    def _calculate_calories(self, speed: float, time_delta: float) -> float:
        """Calculate calories burned based on speed, user weight and MET values"""
        if speed <= 0 or time_delta <= 0:
            return 0.0
        weight_kg = max(40.0, min(150.0, self.user_profile.weight))  # Limit to reasonable range
        if speed < 0.5:
            met = 1.5
        elif speed < 1.0:
            met = 2.0
        elif speed < 1.7:
            met = 2.8
        elif speed < 2.2:
            met = 4.3
        elif speed < 3.0:
            met = 7.0
        elif speed < 4.2:
            met = 9.8
        else:
            met = 11.8
        safe_time_delta = min(1.0, time_delta)
        calories = (met * 3.5 * weight_kg) / (200 * 60) * safe_time_delta
        return min(0.1, calories)

    def _generate_feedback(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Generate real-time feedback based on metrics"""
        feedback = {}

        speed = metrics.get("speed", 0)
        cadence = metrics.get("cadence", 0)
        stride_length = metrics.get("stride_length", 0)
        vertical_oscillation = metrics.get("vertical_oscillation", 0)
        if speed < 1.5:
            feedback["speed"] = "Walking pace detected"
        elif speed < self.target_metrics["speed"] * 0.8:
            feedback["speed"] = "Try to increase your pace"
        elif speed > self.target_metrics["speed"] * 1.5:
            feedback["speed"] = "Great pace! Maintain it if comfortable"
        if cadence > 0:
            if cadence < 150:
                feedback["cadence"] = "Try taking quicker steps"
            elif cadence > 190:
                feedback["cadence"] = "Consider slightly longer strides with fewer steps"
        optimal_stride = self.user_profile.get_stride_length()
        if stride_length > 0 and stride_length < optimal_stride * 0.8:
            feedback["stride"] = "Try to lengthen your stride slightly"
        if vertical_oscillation > 0.1:  # More than 10cm of vertical movement
            feedback["form"] = "Try to reduce vertical bouncing for better efficiency"

        return feedback
