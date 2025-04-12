# CVFit: Computer Vision Fitness Tracker

![CVFit Banner](https://img.shields.io/badge/CVFit-Fitness%20Tracking%20with%20Computer%20Vision-blue?style=for-the-badge&logo=opencv)

## Overview

CVFit is an advanced fitness tracking application that uses computer vision and pose detection to track, analyze, and improve your workout experience. Unlike traditional fitness trackers that require wearable sensors, CVFit leverages your computer's camera to monitor your movements, providing real-time metrics, performance analysis, and workout recommendations.

The app focuses on tracking hand/arm movements to estimate running metrics, making it ideal for indoor workouts where GPS tracking isn't available. Using deep learning-based pose estimation, CVFit delivers a comprehensive fitness experience with minimal setup requirements.

## Key Features

### 🏃‍♂️ Real-time Running Metrics

CVFit captures and displays key running metrics in real-time:

- **Speed**: Calculated from arm movements with machine learning algorithms
- **Distance**: Accumulated based on speed over time
- **Step Count**: Detected from rhythmic arm swing patterns during running
- **Duration**: Precise workout time tracking
- **Calories**: Energy expenditure estimation based on speed and duration

### 📊 Advanced Performance Analysis

The system evaluates several performance dimensions:

- **Stability Score**: Measures the consistency of vertical arm movements
- **Form Analysis**: Evaluates running form by analyzing arm symmetry
- **Efficiency Measurement**: Combines speed and cadence data for overall movement efficiency
- **Consistency Rating**: Tracks variability in pace throughout the session

### 🔍 Pose Detection Technology

- Hand-focused tracking for greater privacy and performance
- Real-time visual feedback with arm/hand keypoint visualization
- Efficient processing optimized for standard webcams

### 📈 Progress Tracking

- Session summaries with key performance metrics
- Historical data tracking across multiple sessions
- Visual performance trends through time-series graphs

## Technical Approach

### Pose Estimation

CVFit employs YOLOv8 for efficient pose estimation, specifically focusing on hand/arm tracking:

- **Model**: YOLOv8n-pose, a lightweight model optimized for real-time inference
- **Keypoints**: Tracks shoulders (5,6), elbows (7,8), and wrists (9,10)
- **Confidence Threshold**: Only uses keypoints with confidence > 0.5 for reliable metrics

### Metrics Calculation

#### Speed Calculation
Speed is derived from arm movement patterns and cadence:

```
speed = arm_movement_speed * 0.7 + (cadence / 160.0) * 2.0
```

Where:
- `arm_movement_speed` is calculated from the displacement of wrist keypoints
- Pixel-to-meter ratio is calibrated based on frame height
- Cadence factor adjusts based on steps per minute

#### Step Detection Algorithm
Steps are counted by identifying the characteristic arm swing patterns during running:

```python
# Simplified representation of the core algorithm
if ((y_vals[1] > y_vals[0] and y_vals[2] > y_vals[1]) or 
    (y_vals[1] < y_vals[0] and y_vals[2] < y_vals[1])) and 
    abs(y_vals[2] - y_vals[0]) > movement_threshold:
    # Step detected
```

The algorithm looks for both "valleys" and "peaks" in wrist vertical position with appropriate cooldown periods to avoid multiple detections of the same step.

#### Calorie Calculation
Calories are estimated using the MET (Metabolic Equivalent of Task) method:

```
calories = (MET × 3.5 × weight_kg) / (200 × 60) × seconds
```

Where MET values vary by speed:
- Walking (< 1.5 m/s): 2.5 METs
- Jogging (1.5-2.5 m/s): 7.0 METs
- Running (2.5-4.0 m/s): 10.0 METs
- Fast running (> 4.0 m/s): 12.5 METs

### Performance Metrics

#### Stability Score (0-95%)
```
stability = base_value + left_arm_stability + right_arm_stability
```
Where each arm's stability is calculated by analyzing variance in vertical position.

#### Form Score (0-90%)
Evaluates symmetry between left and right arm movements, with better scores when arms move in opposite directions (negative correlation coefficient).

#### Efficiency Score (0-95%)
Combines speed and cadence factors, with optimal scores in the 160-180 steps/minute range coupled with good speed.

#### Consistency Score (0-95%)
Calculated from the coefficient of variation (CV) of recent speeds:
```
consistency = 50 + 45 * (1 - CV)
```

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Webcam or built-in camera
- 4GB RAM minimum (8GB recommended for smoother experience)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/S1D007/CVFit
cd CVFit
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Download the pose detection model:
```bash
python download_model.py
```

### Running the Application

Start the application with:

```bash
python gui/app.py
```

## Usage Guide

1. **Launch the application** using the command above
2. **Select your camera source** and preferred resolution
3. **Click "Start Tracking"** to begin your workout session
4. **Run in place** or on a treadmill while facing the camera
5. **Monitor your metrics** on the dashboard in real-time
6. **Click "Stop Tracking"** when finished to save your session

## Technical Architecture

CVFit follows a modular architecture:

- **Core**: Fundamental components for pose detection and motion analysis
  - `pose_engine.py`: YOLOv8-based pose detection
  - `activity_tracker.py`: Converts pose data to fitness metrics
  - `motion_analyzer.py`: Analyzes movement patterns

- **GUI**: User interface components
  - `app.py`: Main application window and UI logic

- **Services**: Backend services for data handling
  - `analytics_service.py`: Session data storage and analysis
  - `recommendation_service.py`: Workout recommendations based on performance
  - `pose_service.py`: WebSocket-based pose data processing

- **Utils**: Helper utilities
  - `pose_utils.py`: Mathematical utilities for pose processing
  - `video_capture.py`: Thread-safe video capture

## Limitations and Constraints

- **Camera Angle**: Requires a clear front view for accurate tracking
- **Lighting Conditions**: Best performance under good lighting
- **Clothing**: Loose or baggy clothing may affect pose detection accuracy
- **Calibration**: Speed calculations are approximate and may require individual calibration
- **Privacy**: While focusing on hands only, still requires camera access
- **Processing Power**: May affect performance on low-end systems

## Future Improvements

### Near-Term Enhancements

- **User Profiles**: Personalized tracking with user-specific parameters
- **Calibration Wizard**: Guide users through customized calibration for more accurate metrics
- **Export Functionality**: Allow exporting workout data to common fitness platforms
- **Voice Feedback**: Audio cues and coaching during workouts

### Long-Term Vision

- **Additional Workout Types**: Support for strength training, yoga, and HIIT exercises
- **Full-Body Analysis**: Optional full-body tracking for comprehensive form analysis
- **Multi-Person Support**: Track multiple users simultaneously
- **Mobile App Version**: Port to mobile platforms for greater accessibility
- **AI Coaching**: Personalized workout recommendations and form corrections
- **VR/AR Integration**: Immersive workout experience with virtual environments

## Acknowledgments

- YOLOv8 team for the pose estimation model
- OpenCV community for computer vision tools
- All contributors and testers who have helped improve CVFit

---

<p align="center">
  <img src="https://img.shields.io/badge/Built%20with-Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Built with Python">
  <img src="https://img.shields.io/badge/Powered%20by-OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="Powered by OpenCV">
  <img src="https://img.shields.io/badge/Uses-YOLOv8-00FFFF?style=flat-square&logo=pytorch&logoColor=white" alt="Uses YOLOv8">
</p>