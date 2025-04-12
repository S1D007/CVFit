from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np

class RecommendationService:
    def __init__(self):
        self.stretching_routines = {
            "pre_run": [
                {"name": "Standing Quad Stretch", "duration": 30},
                {"name": "Forward Leg Swings", "duration": 30},
                {"name": "Lateral Leg Swings", "duration": 30},
                {"name": "Walking Lunges", "duration": 45},
                {"name": "High Knees", "duration": 30}
            ],
            "post_run": [
                {"name": "Calf Stretch", "duration": 30},
                {"name": "Hip Flexor Stretch", "duration": 45},
                {"name": "Hamstring Stretch", "duration": 45},
                {"name": "IT Band Stretch", "duration": 30},
                {"name": "Lower Back Stretch", "duration": 30}
            ]
        }
        
        self.intensity_levels = {
            "low": {"speed": 1.5, "duration": 600},
            "medium": {"speed": 2.5, "duration": 1200},
            "high": {"speed": 3.5, "duration": 1800}
        }

    def get_stretching_routine(self, routine_type: str, fitness_level: str) -> List[Dict]:
        base_routine = self.stretching_routines.get(routine_type, [])
        
        if fitness_level == "advanced":
            return self._modify_routine(base_routine, duration_multiplier=1.5)
        elif fitness_level == "intermediate":
            return self._modify_routine(base_routine, duration_multiplier=1.2)
        return base_routine

    def generate_workout_plan(self, fitness_level: str, 
                            available_time: int,
                            previous_metrics: Optional[Dict] = None) -> Dict:
        base_intensity = self._determine_base_intensity(fitness_level)
        
        if previous_metrics:
            base_intensity = self._adjust_intensity(base_intensity, previous_metrics)
        
        workout_plan = {
            "warm_up": self._generate_warm_up(fitness_level),
            "main_workout": self._generate_main_workout(base_intensity, available_time),
            "cool_down": self._generate_cool_down(fitness_level),
            "stretching": self.get_stretching_routine("post_run", fitness_level)
        }
        
        return workout_plan

    def _modify_routine(self, routine: List[Dict], 
                       duration_multiplier: float) -> List[Dict]:
        return [{
            "name": exercise["name"],
            "duration": int(exercise["duration"] * duration_multiplier)
        } for exercise in routine]

    def _determine_base_intensity(self, fitness_level: str) -> Dict:
        if fitness_level == "advanced":
            return self.intensity_levels["high"]
        elif fitness_level == "intermediate":
            return self.intensity_levels["medium"]
        return self.intensity_levels["low"]

    def _adjust_intensity(self, base_intensity: Dict, 
                         previous_metrics: Dict) -> Dict:
        if previous_metrics.get("completion_rate", 0) > 0.8:
            return {
                "speed": base_intensity["speed"] * 1.1,
                "duration": base_intensity["duration"] * 1.1
            }
        elif previous_metrics.get("completion_rate", 0) < 0.6:
            return {
                "speed": base_intensity["speed"] * 0.9,
                "duration": base_intensity["duration"] * 0.9
            }
        return base_intensity

    def _generate_warm_up(self, fitness_level: str) -> List[Dict]:
        warm_up = self.get_stretching_routine("pre_run", fitness_level)
        warm_up.append({
            "name": "Light Jog",
            "duration": 300 if fitness_level == "advanced" else 180
        })
        return warm_up

    def _generate_main_workout(self, intensity: Dict, 
                             available_time: int) -> List[Dict]:
        workout_time = min(intensity["duration"], 
                          available_time - 600)  # Reserve 10 mins for warm-up/cool-down
        
        if workout_time <= 0:
            return [{"name": "Quick Run", "duration": available_time}]

        return [{
            "name": "Sustained Run",
            "duration": workout_time,
            "target_speed": intensity["speed"]
        }]

    def _generate_cool_down(self, fitness_level: str) -> List[Dict]:
        return [{
            "name": "Walking Cool Down",
            "duration": 300 if fitness_level == "advanced" else 180
        }]