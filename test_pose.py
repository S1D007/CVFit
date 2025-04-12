import cv2
from core.pose_engine import PoseEngine

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Initialize pose engine
    pose_engine = PoseEngine()
    
    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process frame with pose detection
        processed_frame = pose_engine.process_frame(frame)
        
        # Display the result
        cv2.imshow('Pose Detection', processed_frame)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()