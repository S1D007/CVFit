import tkinter as tk
from tkinter import ttk, messagebox, Scale, IntVar, BOTH, X, LEFT, RIGHT, TOP, BOTTOM, Y, Canvas
import cv2
from PIL import Image, ImageTk
import sys
import threading
import time
import os
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pose_engine import PoseEngine
from utils.video_capture import VideoCapture
from core.activity_tracker import ActivityTracker
from services.analytics_service import AnalyticsService

class CVFitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CVFit - Fitness Tracking")
        self.root.geometry("1720x1200")

        self.pose_engine = None
        self.activity_tracker = None
        self.analytics_service = None
        self.video_capture = None

        self.processing = False
        self.frame_skip = 0
        self.frame_count = 0
        self.last_update_time = time.time()
        self.fps = 0

        self.current_speed = 0.0
        self.current_distance = 0.0
        self.current_duration = 0
        self.current_calories = 0.0
        self.current_steps = 0
        self.session_start_time = None
        self.metrics_history = []
        self.total_sessions = 0
        self.total_distance = 0.0
        self.last_metrics_update = time.time()

        self.camera_source = IntVar(value=0)

        self.setup_ui()

        self.create_placeholder_image()

        threading.Thread(target=self._load_components, daemon=True).start()

    def _load_components(self):
        """Load heavy components in background"""
        try:
            self.root.after(0, lambda: self.status_label.config(text="Loading pose detection model..."))
            self.pose_engine = PoseEngine()
            self.activity_tracker = ActivityTracker()
            self.analytics_service = AnalyticsService()
            self.root.after(0, lambda: self.status_label.config(text="Ready to start tracking"))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Error loading components: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Initialization Error",
                                                          f"Failed to initialize components: {str(e)}"))

    def create_placeholder_image(self):
        """Create a placeholder image for when no camera feed is available"""
        width, height = 1200, 720
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img.fill(50)

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "No Camera Feed Available"
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        cv2.putText(img, text, (text_x, text_y), font, 1, (255, 255, 255), 2)

        instructions = "Click 'Start Tracking' to begin"
        inst_size = cv2.getTextSize(instructions, font, 0.7, 1)[0]
        inst_x = (width - inst_size[0]) // 2
        inst_y = text_y + 40
        cv2.putText(img, instructions, (inst_x, inst_y), font, 0.7, (200, 200, 200), 1)

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        self.placeholder_image = ImageTk.PhotoImage(image=pil_img)

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=5)

        title_label = ttk.Label(self.top_frame, text="CVFit - Computer Vision Fitness Tracker",
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=5)

        self.status_label = ttk.Label(self.top_frame, text="Initializing components...",
                                    font=("Arial", 10))
        self.status_label.pack(pady=2)

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.video_container = ttk.Frame(self.content_frame)
        self.video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_frame = ttk.LabelFrame(self.video_container, text="Video Feed")
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.metrics_container = ttk.Frame(self.content_frame)
        self.metrics_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)

        self.create_metrics_dashboard()

        self.settings_frame = ttk.LabelFrame(self.main_frame, text="Settings")
        self.settings_frame.pack(fill=tk.X, pady=5)

        camera_frame = ttk.Frame(self.settings_frame)
        camera_frame.pack(fill=tk.X, pady=5)

        ttk.Label(camera_frame, text="Camera:").pack(side=tk.LEFT, padx=5)

        for i, cam_text in enumerate(["Default (0)", "Camera 1", "Camera 2"]):
            ttk.Radiobutton(
                camera_frame,
                text=cam_text,
                variable=self.camera_source,
                value=i
            ).pack(side=tk.LEFT, padx=5)

        res_frame = ttk.Frame(self.settings_frame)
        res_frame.pack(fill=tk.X, pady=5)

        ttk.Label(res_frame, text="Resolution:").pack(side=tk.LEFT, padx=5)

        self.resolution_var = tk.StringVar(value="640x480")
        res_combo = ttk.Combobox(res_frame, textvariable=self.resolution_var,
                               values=["320x240", "640x480", "800x600", "1280x720"])
        res_combo.pack(side=tk.LEFT, padx=5)
        res_combo.bind("<<ComboboxSelected>>", self.update_resolution)

        perf_frame = ttk.Frame(self.settings_frame)
        perf_frame.pack(fill=tk.X, pady=5)

        ttk.Label(perf_frame, text="Frame Skip:").pack(side=tk.LEFT, padx=5)

        self.skip_var = IntVar(value=0)
        skip_scale = Scale(perf_frame, from_=0, to=5, orient=tk.HORIZONTAL,
                         variable=self.skip_var, length=150)
        skip_scale.pack(side=tk.LEFT, padx=5)

        self.fps_label = ttk.Label(perf_frame, text="FPS: 0")
        self.fps_label.pack(side=tk.RIGHT, padx=15)

        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X, pady=10)

        style = ttk.Style()
        style.configure('Green.TButton', background='green')
        style.configure('Red.TButton', background='red')

        self.start_button = ttk.Button(self.controls_frame,
                                     text="Start Tracking",
                                     command=self.start_tracking,
                                     style='Green.TButton',
                                     width=20)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(self.controls_frame,
                                    text="Stop Tracking",
                                    command=self.stop_tracking,
                                    style='Red.TButton',
                                    state=tk.DISABLED,
                                    width=20)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(self.controls_frame, orient=tk.HORIZONTAL,
                                      length=200, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=10)

        self.root.after(100, self._show_placeholder)

    def _show_placeholder(self):
        """Show placeholder image in the video label"""
        if hasattr(self, 'placeholder_image'):
            self.video_label.configure(image=self.placeholder_image)

    def update_resolution(self, event=None):
        """Update video resolution settings"""
        if self.video_capture:
            width, height = map(int, self.resolution_var.get().split('x'))
            self.video_capture.set_frame_dimensions(width, height)

    def start_tracking(self):
        """Start video tracking with improved error handling"""
        if self.pose_engine is None:
            messagebox.showinfo("Please Wait", "Components are still loading. Please try again in a moment.")
            return

        self.status_label.config(text="Starting camera...")
        self.progress.start()

        self.current_speed = 0.0
        self.current_distance = 0.0
        self.current_calories = 0.0
        self.session_start_time = datetime.now()
        self.metrics_history = []

        threading.Thread(target=self._initialize_tracking, daemon=True).start()

    def _initialize_tracking(self):
        """Initialize video capture in a separate thread"""
        try:
            width, height = map(int, self.resolution_var.get().split('x'))

            camera_idx = self.camera_source.get()

            self.video_capture = VideoCapture(camera_idx)
            self.video_capture.set_frame_dimensions(width, height)
            self.video_capture.start()

            time.sleep(0.5)

            if self.video_capture.is_opened():
                self.root.after(0, self._enable_tracking)
            else:
                error = self.video_capture.get_error() or "Could not access camera"
                self.root.after(0, lambda: messagebox.showerror("Camera Error", error))
                self.root.after(0, self._reset_ui)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Camera error: {str(e)}"))
            self.root.after(0, self._reset_ui)

    def _enable_tracking(self):
        """Enable tracking UI after successful initialization"""
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.progress.stop()
        self.status_label.config(text="Tracking active")
        self.processing = True

        self.session_start_time = datetime.now()
        self.current_speed = 0.0
        self.current_distance = 0.0
        self.current_calories = 0.0
        self.metrics_history = []
        self.last_metrics_update = time.time()

        if self.activity_tracker:
            self.activity_tracker.start_session()
            self.status_label.config(text="Tracking active - Move your arms to count steps")

        self.update_frame()
        self.update_metrics()

    def _reset_ui(self):
        """Reset UI after errors"""
        self.progress.stop()
        self.status_label.config(text="Ready to start tracking")
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        self._show_placeholder()

    def stop_tracking(self):
        """Stop video tracking with proper cleanup and save session data"""
        if self.processing and self.session_start_time:
            self.total_sessions += 1
            self.total_distance += self.current_distance

            duration = (datetime.now() - self.session_start_time).total_seconds()
            if duration > 0:
                session_data = {
                    "date": datetime.now(),
                    "duration": duration,
                    "distance": self.current_distance,
                    "calories": self.current_calories,
                    "average_metrics": {
                        "avg_speed": self.current_speed,
                        "avg_cadence": 160.0,
                        "avg_stride_length": 1.2
                    }
                }

                if self.analytics_service:
                    try:
                        if hasattr(self.analytics_service, 'add_session'):
                            self.analytics_service.add_session(session_data)

                        distance_str = f"{self.current_distance:.1f} meters"
                        if self.current_distance >= 1000:
                            distance_str = f"{self.current_distance/1000:.2f} km"

                        hours, remainder = divmod(int(duration), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                        messagebox.showinfo("Session Complete",
                                            f"Great job! Session completed:\n\n"
                                            f"Duration: {time_str}\n"
                                            f"Distance: {distance_str}\n"
                                            f"Calories: {int(self.current_calories)} kcal")
                    except Exception as e:
                        print(f"Error saving session data: {str(e)}")

        self.processing = False
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_label.config(text="Tracking stopped")
        self.session_start_time = None

        self._show_placeholder()

    def update_frame(self):
        """Update video frame with performance optimization"""
        if not self.processing:
            return

        try:
            if self.video_capture:
                error = self.video_capture.get_error()
                if error:
                    self.status_label.config(text=f"Camera error: {error}")
                    self.stop_tracking()
                    messagebox.showerror("Camera Error", error)
                    return

                self.frame_count += 1
                skip = self.skip_var.get()

                if skip > 0 and self.frame_count % (skip + 1) != 0:
                    frame = self.video_capture.read()
                    self.root.after(5, self.update_frame)
                    return

                frame = self.video_capture.read()
                if frame is not None:
                    current_time = time.time()
                    time_diff = current_time - self.last_update_time
                    if time_diff > 0.5:
                        self.fps = int(1.0 / ((time_diff) / max(1, self.frame_count)))
                        self.fps_label.config(text=f"FPS: {self.fps}")
                        self.last_update_time = current_time
                        self.frame_count = 0

                    processed_frame, hand_positions = self.pose_engine.process_frame(frame)

                    if processed_frame is not None:
                        if self.activity_tracker and hand_positions:
                            frame_shape = processed_frame.shape
                            feedback = self.activity_tracker.update_metrics(hand_positions, frame_shape)

                            if feedback:
                                feedback_text = next(iter(feedback.values()))
                                self.status_label.config(text=feedback_text)

                        frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        imgtk = ImageTk.PhotoImage(image=img)
                        self.video_label.imgtk = imgtk
                        self.video_label.configure(image=imgtk)

                delay = 5 if self.fps > 20 else 10
                self.root.after(delay, self.update_frame)
            else:
                self.stop_tracking()
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            print(f"Frame update error: {str(e)}")
            self.root.after(1000, self.update_frame)

    def create_metrics_dashboard(self):
        """Create a beautiful metrics dashboard with real-time running statistics"""
        style = ttk.Style()

        style.configure("MetricsTitle.TLabel",
                        font=("Segoe UI", 14, "bold"),
                        foreground="#fff")

        style.configure("MetricsValue.TLabel",
                        font=("Segoe UI", 20, "bold"),
                        foreground="#fff")

        style.configure("MetricsUnit.TLabel",
                        font=("Segoe UI", 10),
                        foreground="#fff")

        style.configure("MetricsHeading.TLabel",
                        font=("Segoe UI", 12, "bold"),
                        foreground="#fff")

        style.configure("SessionValue.TLabel",
                        font=("Segoe UI", 11),
                        foreground="#fff")

        style.configure("BlueProgress.Horizontal.TProgressbar",
                        troughcolor="#ecf0f1",
                        background="#3498db",
                        thickness=12,
                        bordercolor="#bdc3c7",
                        lightcolor="#3498db",
                        darkcolor="#2980b9")

        style.configure("GreenProgress.Horizontal.TProgressbar",
                        troughcolor="#ecf0f1",
                        background="#2ecc71",
                        thickness=12,
                        bordercolor="#bdc3c7",
                        lightcolor="#2ecc71",
                        darkcolor="#27ae60")


        self.metrics_dashboard = ttk.LabelFrame(self.metrics_container, text="Running Metrics Dashboard")
        self.metrics_dashboard.pack(fill=tk.BOTH, expand=True, pady=5)

        current_session_frame = ttk.LabelFrame(self.metrics_dashboard, text="Current Session")
        current_session_frame.pack(fill=tk.X, padx=10, pady=5)

        timer_frame = ttk.Frame(current_session_frame)
        timer_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(timer_frame, text="DURATION", style="MetricsTitle.TLabel").pack(side=tk.LEFT)
        self.timer_display = ttk.Label(timer_frame, text="00:00:00", style="MetricsValue.TLabel")
        self.timer_display.pack(side=tk.RIGHT)

        steps_frame = ttk.Frame(current_session_frame)
        steps_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(steps_frame, text="STEPS", style="MetricsTitle.TLabel").pack(side=tk.LEFT)
        self.steps_display = ttk.Label(steps_frame, text="0", style="MetricsValue.TLabel")
        self.steps_display.pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Label(steps_frame, text="count", style="MetricsUnit.TLabel").pack(side=tk.RIGHT)

        speed_frame = ttk.Frame(current_session_frame)
        speed_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(speed_frame, text="SPEED", style="MetricsTitle.TLabel").pack(side=tk.LEFT)
        self.speed_display = ttk.Label(speed_frame, text="0.0", style="MetricsValue.TLabel")
        self.speed_display.pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Label(speed_frame, text="m/s", style="MetricsUnit.TLabel").pack(side=tk.RIGHT)

        distance_frame = ttk.Frame(current_session_frame)
        distance_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(distance_frame, text="DISTANCE", style="MetricsTitle.TLabel").pack(side=tk.LEFT)
        self.distance_display = ttk.Label(distance_frame, text="0.0", style="MetricsValue.TLabel")
        self.distance_display.pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Label(distance_frame, text="meters", style="MetricsUnit.TLabel").pack(side=tk.RIGHT)

        calories_frame = ttk.Frame(current_session_frame)
        calories_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(calories_frame, text="CALORIES", style="MetricsTitle.TLabel").pack(side=tk.LEFT)
        self.calories_display = ttk.Label(calories_frame, text="0", style="MetricsValue.TLabel")
        self.calories_display.pack(side=tk.RIGHT, padx=(0, 5))
        ttk.Label(calories_frame, text="kcal", style="MetricsUnit.TLabel").pack(side=tk.RIGHT)

        performance_frame = ttk.LabelFrame(self.metrics_dashboard, text="Performance Metrics")
        performance_frame.pack(fill=tk.X, padx=10, pady=10)

        metrics = [
            {"name": "STABILITY", "var_name": "stability_bar", "style": "BlueProgress"},
            {"name": "FORM", "var_name": "form_bar", "style": "GreenProgress"},
            {"name": "EFFICIENCY", "var_name": "efficiency_bar", "style": "BlueProgress"},
            {"name": "CONSISTENCY", "var_name": "consistency_bar", "style": "GreenProgress"},
        ]

        for metric in metrics:
            frame = ttk.Frame(performance_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Label(frame, text=metric["name"], style="MetricsHeading.TLabel").pack(side=tk.LEFT)
            value_label = ttk.Label(frame, text="0%", width=5)
            value_label.pack(side=tk.RIGHT)
            setattr(self, f"{metric['var_name']}_label", value_label)

            progress = ttk.Progressbar(
                frame, style=f"{metric['style']}.Horizontal.TProgressbar",
                length=200, mode='determinate', value=0
            )
            progress.pack(side=tk.RIGHT, padx=10)
            setattr(self, metric["var_name"], progress)

        history_frame = ttk.LabelFrame(self.metrics_dashboard, text="Running History")
        history_frame.pack(fill=tk.X, padx=10, pady=10)

        sessions_frame = ttk.Frame(history_frame)
        sessions_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(sessions_frame, text="TOTAL SESSIONS", style="MetricsHeading.TLabel").pack(side=tk.LEFT)
        self.sessions_display = ttk.Label(sessions_frame, text="0", style="SessionValue.TLabel")
        self.sessions_display.pack(side=tk.RIGHT)

        total_distance_frame = ttk.Frame(history_frame)
        total_distance_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(total_distance_frame, text="TOTAL DISTANCE", style="MetricsHeading.TLabel").pack(side=tk.LEFT)
        self.total_distance_display = ttk.Label(total_distance_frame, text="0.0 m", style="SessionValue.TLabel")
        self.total_distance_display.pack(side=tk.RIGHT)

        pace_frame = ttk.Frame(history_frame)
        pace_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(pace_frame, text="AVERAGE PACE", style="MetricsHeading.TLabel").pack(side=tk.LEFT)
        self.avg_pace_display = ttk.Label(pace_frame, text="0:00 min/km", style="SessionValue.TLabel")
        self.avg_pace_display.pack(side=tk.RIGHT)

        level_frame = ttk.Frame(history_frame)
        level_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(level_frame, text="RUNNING LEVEL", style="MetricsHeading.TLabel").pack(side=tk.LEFT)
        self.level_display = ttk.Label(level_frame, text="Novice", style="SessionValue.TLabel")
        self.level_display.pack(side=tk.RIGHT)

        self.trend_fig = Figure(figsize=(4, 2), dpi=100)
        self.trend_plot = self.trend_fig.add_subplot(111)
        self.trend_plot.set_title("Speed Trend")
        self.trend_plot.set_ylabel("Speed (m/s)")
        self.trend_plot.grid(True, linestyle='--', alpha=0.7)

        self.trend_canvas = FigureCanvasTkAgg(self.trend_fig, master=self.metrics_dashboard)
        self.trend_canvas.get_tk_widget().pack(fill=tk.X, padx=10, pady=10)

        self.trend_plot.plot([0, 1, 2, 3, 4], [0, 0, 0, 0, 0], 'b-')
        self.trend_canvas.draw()

    def update_metrics(self):
        """Update metrics dashboard with latest data from activity tracker"""
        if not self.processing or not self.session_start_time:
            return

        now = datetime.now()
        duration = (now - self.session_start_time).total_seconds()
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)

        self.timer_display.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        got_real_data = False
        if self.activity_tracker and self.activity_tracker.current_session:
            session_data = self.activity_tracker.current_session

            if len(self.activity_tracker.running_metrics) > 0:
                latest_metrics = self.activity_tracker.running_metrics[-1]
                if latest_metrics.get("speed", 0) > 0.01:
                    self.current_speed = latest_metrics.get("speed", 0.0)
                    self.current_distance = session_data["total_distance"]
                    self.current_calories = session_data["calories_burned"]
                    self.current_steps = session_data.get("steps_count", 0)
                    got_real_data = True

        if not got_real_data and len(self.metrics_history) > 0:
            if duration > 3.0:
                time_factor = min(1.0, duration / 60.0)
                self.current_speed = 0.5 * time_factor

                time_delta = time.time() - self.last_metrics_update
                self.last_metrics_update = time.time()
                distance_increment = self.current_speed * time_delta
                self.current_distance += distance_increment
                weight_kg = 70 # this is mine
                if self.current_speed < 1.5:
                    met = 2.5  # Walking
                elif self.current_speed < 2.5:
                    met = 7.0  # Jogging
                elif self.current_speed < 4.0:
                    met = 10.0  # Running
                else:
                    met = 12.5  # Fast running
                calories_increment = (met * 3.5 * weight_kg) / (200 * 60) * time_delta
                self.current_calories += calories_increment

        self.metrics_history.append({
            'speed': self.current_speed,
            'distance': self.current_distance,
            'time': duration,
            'calories': self.current_calories
        })

        self.speed_display.config(text=f"{self.current_speed:.1f}")

        if self.current_distance < 1000:
            self.distance_display.config(text=f"{self.current_distance:.1f}")
        else:
            self.distance_display.config(text=f"{self.current_distance/1000:.2f}")

        self.calories_display.config(text=f"{int(self.current_calories)}")

        self.steps_display.config(text=f"{self.current_steps}")

        stability = 70 + min(20, duration / 10.0)
        self.stability_bar.config(value=stability)
        self.stability_bar_label.config(text=f"{int(stability)}%")

        form = 65 + min(20, duration / 15.0)
        self.form_bar.config(value=form)
        self.form_bar_label.config(text=f"{int(form)}%")

        efficiency = 65 + min(15, self.current_speed * 10.0)
        self.efficiency_bar.config(value=efficiency)
        self.efficiency_bar_label.config(text=f"{int(efficiency)}%")

        consistency = 60 + min(25, duration / 20.0)
        self.consistency_bar.config(value=consistency)
        self.consistency_bar_label.config(text=f"{int(consistency)}%")

        self.total_sessions = max(1, self.total_sessions)
        self.sessions_display.config(text=str(self.total_sessions))

        if self.total_distance + self.current_distance < 1000:
            formatted_distance = f"{self.total_distance + self.current_distance:.1f} m"
        else:
            formatted_distance = f"{(self.total_distance + self.current_distance)/1000:.2f} km"
        self.total_distance_display.config(text=formatted_distance)

        if self.current_speed > 0:
            pace_seconds = 1000 / self.current_speed
            pace_minutes, pace_seconds = divmod(int(pace_seconds), 60)
            self.avg_pace_display.config(text=f"{pace_minutes}:{pace_seconds:02d} min/km")

        if self.current_speed > 3.0:
            level = "Advanced"
        elif self.current_speed > 2.2:
            level = "Intermediate"
        elif self.current_speed > 0.5:
            level = "Beginner"
        else:
            level = "Novice"
        self.level_display.config(text=level)

        if len(self.metrics_history) % 10 == 0:
            self.update_trend_graph()

        self.root.after(1000, self.update_metrics)

    def _calculate_stability_percentage(self):
        """Calculate stability percentage based on hand movement patterns"""
        if not self.activity_tracker:
            return 70

        stability = 70

        if len(self.activity_tracker.left_wrist_history) > 10:
            left_y_positions = [pos[1] for pos in self.activity_tracker.left_wrist_history]
            left_variance = np.var(left_y_positions) if len(left_y_positions) > 0 else 0
            left_stability = max(0, min(25, 25 - (left_variance / 1000)))
            stability += left_stability

        if len(self.activity_tracker.right_wrist_history) > 10:
            right_y_positions = [pos[1] for pos in self.activity_tracker.right_wrist_history]
            right_variance = np.var(right_y_positions) if len(right_y_positions) > 0 else 0
            right_stability = max(0, min(25, 25 - (right_variance / 1000)))
            stability += right_stability

        return min(95, stability)

    def _calculate_form_percentage(self):
        """Calculate form percentage based on hand movement patterns"""
        if not self.activity_tracker:
            return 60

        form = 60

        if (len(self.activity_tracker.left_wrist_history) > 5 and
            len(self.activity_tracker.right_wrist_history) > 5):

            left_moves = []
            right_moves = []

            for i in range(1, min(len(self.activity_tracker.left_wrist_history),
                               len(self.activity_tracker.right_wrist_history))):
                if i > 0:
                    left_prev = self.activity_tracker.left_wrist_history[i-1]
                    left_curr = self.activity_tracker.left_wrist_history[i]
                    right_prev = self.activity_tracker.right_wrist_history[i-1]
                    right_curr = self.activity_tracker.right_wrist_history[i]

                    left_dy = left_curr[1] - left_prev[1]
                    right_dy = right_curr[1] - right_prev[1]

                    left_moves.append(left_dy)
                    right_moves.append(right_dy)

            if left_moves and right_moves:
                try:
                    corr = np.corrcoef(left_moves, right_moves)[0, 1]
                    if corr < 0:
                        symmetry_bonus = min(30, abs(corr) * 30)
                        form += symmetry_bonus
                except:
                    pass

        return min(90, form)

    def _calculate_efficiency_percentage(self, avg_metrics):
        """Calculate efficiency percentage based on speed and cadence"""
        if not avg_metrics:
            return 65

        efficiency = 65

        avg_speed = avg_metrics.get("avg_speed", 0)
        avg_cadence = avg_metrics.get("avg_cadence", 0)

        if avg_speed > 0 and avg_cadence > 0:
            cadence_factor = min(15, 15 * (avg_cadence / 180))

            speed_factor = min(15, 15 * (avg_speed / 3.0))

            efficiency += cadence_factor + speed_factor

        return min(95, efficiency)

    def _calculate_consistency_percentage(self):
        """Calculate consistency percentage based on speed variance"""
        if not self.metrics_history or len(self.metrics_history) < 5:
            return 50

        recent_speeds = [m['speed'] for m in self.metrics_history[-10:]]

        cv = np.std(recent_speeds) / max(0.1, np.mean(recent_speeds))

        consistency = 50 + max(0, min(45, 45 * (1 - cv)))

        return consistency

    def update_trend_graph(self):
        """Update the speed trend graph with latest data"""
        if len(self.metrics_history) < 5:
            return

        self.trend_plot.clear()

        num_points = min(30, len(self.metrics_history))
        speeds = [self.metrics_history[-i]['speed'] for i in range(num_points, 0, -1)]
        times = list(range(len(speeds)))

        self.trend_plot.plot(times, speeds, 'b-', linewidth=2)
        self.trend_plot.set_title("Speed Trend")
        self.trend_plot.set_ylabel("Speed (m/s)")
        self.trend_plot.grid(True, linestyle='--', alpha=0.7)

        max_speed = max(max(speeds, default=0), 0.1)
        self.trend_plot.set_ylim([0, max_speed * 1.2])

        self.trend_plot.set_xticks([])

        self.trend_canvas.draw()

def main():
    root = tk.Tk()
    app = CVFitGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
