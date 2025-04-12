from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class UserPreferences:
    preferred_workout_time: int = 1800
    preferred_intensity: str = "medium"
    notification_enabled: bool = True
    target_weekly_sessions: int = 3

@dataclass
class FitnessMetrics:
    average_speed: float = 0.0
    average_cadence: float = 0.0
    total_distance: float = 0.0
    total_duration: int = 0
    sessions_completed: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class User:
    id: str
    name: str
    height: float
    weight: float
    fitness_level: str = "novice"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    metrics: FitnessMetrics = field(default_factory=FitnessMetrics)
    workout_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def update_metrics(self, session_data: Dict) -> None:
        self.metrics.total_distance += session_data["total_distance"]
        self.metrics.total_duration += session_data["duration"]
        self.metrics.sessions_completed += 1
        
        n = self.metrics.sessions_completed
        self.metrics.average_speed = (
            (self.metrics.average_speed * (n - 1) + 
             session_data["average_metrics"]["avg_speed"]) / n
        )
        self.metrics.average_cadence = (
            (self.metrics.average_cadence * (n - 1) + 
             session_data["average_metrics"]["avg_cadence"]) / n
        )
        self.metrics.last_updated = datetime.now()
        
        self.workout_history.append(session_data)
        self._update_fitness_level()

    def _update_fitness_level(self) -> None:
        if self.metrics.sessions_completed < 5:
            return

        recent_speed = sum(s["average_metrics"]["avg_speed"] 
                          for s in self.workout_history[-5:]) / 5
        
        if recent_speed > 3.2:
            self.fitness_level = "advanced"
        elif recent_speed > 2.5:
            self.fitness_level = "intermediate"
        else:
            self.fitness_level = "novice"