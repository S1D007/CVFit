from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self):
        self.workout_history = []
        self.performance_thresholds = {
            "novice": {"speed": 1.8, "cadence": 140},
            "intermediate": {"speed": 2.5, "cadence": 160},
            "advanced": {"speed": 3.2, "cadence": 180}
        }

    def add_workout_session(self, session_data: Dict) -> None:
        session_data["timestamp"] = datetime.now()
        self.workout_history.append(session_data)

    def get_performance_level(self, recent_sessions: int = 5) -> str:
        if not self.workout_history:
            return "novice"

        recent_data = self.workout_history[-recent_sessions:]
        avg_speed = np.mean([s["average_metrics"]["avg_speed"] for s in recent_data])
        avg_cadence = np.mean([s["average_metrics"]["avg_cadence"] for s in recent_data])

        if avg_speed >= self.performance_thresholds["advanced"]["speed"] and \
           avg_cadence >= self.performance_thresholds["advanced"]["cadence"]:
            return "advanced"
        elif avg_speed >= self.performance_thresholds["intermediate"]["speed"] and \
             avg_cadence >= self.performance_thresholds["intermediate"]["cadence"]:
            return "intermediate"
        return "novice"

    def generate_recommendations(self) -> Dict[str, str]:
        if not self.workout_history:
            return {
                "workout": "Start with a 10-minute light jog to establish baseline",
                "intensity": "low",
                "focus": "form and breathing"
            }

        performance_level = self.get_performance_level()
        last_session = self.workout_history[-1]
        
        recommendations = {
            "novice": {
                "workout": "20-minute steady-state run",
                "intensity": "moderate",
                "focus": "maintaining consistent pace"
            },
            "intermediate": {
                "workout": "30-minute run with interval training",
                "intensity": "high",
                "focus": "speed variations and endurance"
            },
            "advanced": {
                "workout": "45-minute complex training session",
                "intensity": "very high",
                "focus": "performance optimization"
            }
        }

        return recommendations[performance_level]

    def get_progress_metrics(self, days: int = 30) -> Dict:
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_sessions = [s for s in self.workout_history 
                           if s["timestamp"] > cutoff_date]

        if not relevant_sessions:
            return {}

        speeds = [s["average_metrics"]["avg_speed"] for s in relevant_sessions]
        distances = [s["total_distance"] for s in relevant_sessions]
        durations = [s["duration"] for s in relevant_sessions]

        return {
            "avg_speed_trend": np.polyfit(range(len(speeds)), speeds, 1)[0],
            "total_distance": sum(distances),
            "total_duration": sum(durations),
            "sessions_count": len(relevant_sessions),
            "improvement_rate": self._calculate_improvement_rate(relevant_sessions)
        }

    def _calculate_improvement_rate(self, sessions: List[Dict]) -> float:
        if len(sessions) < 2:
            return 0.0

        first_speed = sessions[0]["average_metrics"]["avg_speed"]
        last_speed = sessions[-1]["average_metrics"]["avg_speed"]
        
        return (last_speed - first_speed) / first_speed * 100