from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid

@dataclass
class WorkoutPhase:
    name: str
    duration: int
    target_speed: Optional[float] = None
    target_cadence: Optional[float] = None
    completed: bool = False

@dataclass
class Workout:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    phases: List[WorkoutPhase] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    
    def start(self) -> None:
        self.start_time = datetime.now()
        self.metrics = {
            "total_distance": 0.0,
            "average_speed": 0.0,
            "average_cadence": 0.0,
            "calories_burned": 0.0,
            "stability_score": 0.0
        }

    def end(self) -> None:
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).seconds

    def update_metrics(self, frame_metrics: Dict) -> None:
        n = len(self.metrics.get("speed_samples", []))
        
        self.metrics.setdefault("speed_samples", []).append(
            frame_metrics.get("speed", 0))
        self.metrics.setdefault("cadence_samples", []).append(
            frame_metrics.get("cadence", 0))
        self.metrics.setdefault("stability_samples", []).append(
            frame_metrics.get("stability", 0))

        self.metrics["average_speed"] = sum(self.metrics["speed_samples"]) / (n + 1)
        self.metrics["average_cadence"] = sum(self.metrics["cadence_samples"]) / (n + 1)
        self.metrics["stability_score"] = sum(self.metrics["stability_samples"]) / (n + 1)
        
        if "speed" in frame_metrics:
            self.metrics["total_distance"] += frame_metrics["speed"] * (1/30)  # Assuming 30 FPS

    def get_completion_rate(self) -> float:
        completed_phases = sum(1 for phase in self.phases if phase.completed)
        return completed_phases / len(self.phases) if self.phases else 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration if hasattr(self, "duration") else None,
            "metrics": self.metrics,
            "completion_rate": self.get_completion_rate()
        }