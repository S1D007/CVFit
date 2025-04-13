from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class UserPreferences:
    dark_mode: bool = True
    show_metrics_dashboard: bool = True
    auto_save_sessions: bool = True
    notification_enabled: bool = True

@dataclass
class FitnessMetrics:
    total_distance: float = 0.0
    total_duration: float = 0.0
    total_calories: float = 0.0
    total_steps: int = 0
    average_speed: float = 0.0
    average_cadence: float = 0.0
    sessions_completed: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class UserProfile:
    """User profile for personalized metrics calculations"""
    height: float = 170.0  # height in cm
    weight: float = 70.0   # weight in kg
    age: int = 30
    gender: str = "other"  # male, female, other
    stride_multiplier: float = 0.415  # average stride length multiplier (stride = height * multiplier)

    def get_stride_length(self) -> float:
        """Calculate estimated stride length based on height"""
        return self.height * self.stride_multiplier / 100.0

    def get_bmr(self) -> float:
        """Calculate Basal Metabolic Rate using the Mifflin-St Jeor Equation"""
        if self.gender.lower() == "male":
            return (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
        elif self.gender.lower() == "female":
            return (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161
        else:
            male_bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5
            female_bmr = (10 * self.weight) + (6.25 * self.height) - (5 * self.age) - 161
            return (male_bmr + female_bmr) / 2

@dataclass
class User:
    id: str
    name: str
    height: float
    weight: float
    fitness_level: str = "novice"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    metrics: FitnessMetrics = field(default_factory=FitnessMetrics)
    profile: UserProfile = field(default_factory=UserProfile)
    workout_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.profile.height = self.height
        self.profile.weight = self.weight

    def update_metrics(self, session_data: Dict) -> None:
        self.metrics.total_distance += session_data["total_distance"]
        self.metrics.total_duration += session_data["duration"]
        self.metrics.sessions_completed += 1
        self.metrics.total_steps += session_data["steps_count"]
        self.metrics.total_calories += session_data["calories_burned"]

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

    def update_profile(self, profile_data: Dict) -> None:
        """Update user profile with new information"""
        if "height" in profile_data:
            self.height = profile_data["height"]
            self.profile.height = profile_data["height"]
        if "weight" in profile_data:
            self.weight = profile_data["weight"]
            self.profile.weight = profile_data["weight"]
        if "age" in profile_data:
            self.profile.age = profile_data["age"]
        if "gender" in profile_data:
            self.profile.gender = profile_data["gender"]
        if "stride_multiplier" in profile_data:
            self.profile.stride_multiplier = profile_data["stride_multiplier"]

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
