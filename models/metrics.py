from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

@dataclass
class RunningMetrics:
    speed: float
    cadence: float
    stride_length: float
    vertical_oscillation: float
    ground_contact_time: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceMetrics:
    stability_score: float = 0.0
    form_score: float = 0.0
    efficiency_score: float = 0.0
    consistency_score: float = 0.0
    
    def calculate_overall_score(self) -> float:
        weights = {
            'stability': 0.3,
            'form': 0.3,
            'efficiency': 0.2,
            'consistency': 0.2
        }
        return (
            self.stability_score * weights['stability'] +
            self.form_score * weights['form'] +
            self.efficiency_score * weights['efficiency'] +
            self.consistency_score * weights['consistency']
        )

class MetricsAnalyzer:
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.metrics_buffer: List[RunningMetrics] = []

    def add_metrics(self, metrics: RunningMetrics) -> None:
        self.metrics_buffer.append(metrics)
        if len(self.metrics_buffer) > self.window_size:
            self.metrics_buffer.pop(0)

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        if not self.metrics_buffer:
            return PerformanceMetrics()

        stability = self._calculate_stability()
        form = self._calculate_form()
        efficiency = self._calculate_efficiency()
        consistency = self._calculate_consistency()

        return PerformanceMetrics(
            stability_score=stability,
            form_score=form,
            efficiency_score=efficiency,
            consistency_score=consistency
        )

    def _calculate_stability(self) -> float:
        if len(self.metrics_buffer) < 2:
            return 0.0

        vertical_oscillations = [m.vertical_oscillation for m in self.metrics_buffer]
        stability = 1.0 - min(1.0, np.std(vertical_oscillations) / 0.05)
        return max(0.0, stability)

    def _calculate_form(self) -> float:
        if not self.metrics_buffer:
            return 0.0

        stride_lengths = [m.stride_length for m in self.metrics_buffer]
        ground_contacts = [m.ground_contact_time for m in self.metrics_buffer]
        
        stride_consistency = 1.0 - min(1.0, np.std(stride_lengths) / 0.1)
        contact_efficiency = 1.0 - min(1.0, np.mean(ground_contacts) / 0.3)
        
        return (stride_consistency + contact_efficiency) / 2

    def _calculate_efficiency(self) -> float:
        if not self.metrics_buffer:
            return 0.0

        speeds = [m.speed for m in self.metrics_buffer]
        cadences = [m.cadence for m in self.metrics_buffer]
        
        speed_efficiency = min(1.0, np.mean(speeds) / 3.0)
        cadence_efficiency = min(1.0, np.mean(cadences) / 180.0)
        
        return (speed_efficiency + cadence_efficiency) / 2

    def _calculate_consistency(self) -> float:
        if len(self.metrics_buffer) < self.window_size:
            return 0.0

        speeds = [m.speed for m in self.metrics_buffer]
        cadences = [m.cadence for m in self.metrics_buffer]
        
        speed_consistency = 1.0 - min(1.0, np.std(speeds) / 0.5)
        cadence_consistency = 1.0 - min(1.0, np.std(cadences) / 10.0)
        
        return (speed_consistency + cadence_consistency) / 2

    def get_trend_analysis(self) -> Dict:
        if len(self.metrics_buffer) < 2:
            return {}

        speeds = [m.speed for m in self.metrics_buffer]
        cadences = [m.cadence for m in self.metrics_buffer]
        
        speed_trend = np.polyfit(range(len(speeds)), speeds, 1)[0]
        cadence_trend = np.polyfit(range(len(cadences)), cadences, 1)[0]
        
        return {
            "speed_trend": speed_trend,
            "cadence_trend": cadence_trend,
            "fatigue_indicator": self._calculate_fatigue_indicator()
        }

    def _calculate_fatigue_indicator(self) -> float:
        if len(self.metrics_buffer) < self.window_size:
            return 0.0

        recent_metrics = self.metrics_buffer[-int(self.window_size/2):]
        older_metrics = self.metrics_buffer[:int(self.window_size/2)]
        
        recent_efficiency = np.mean([m.speed / m.cadence for m in recent_metrics])
        older_efficiency = np.mean([m.speed / m.cadence for m in older_metrics])
        
        return max(0.0, (older_efficiency - recent_efficiency) / older_efficiency)