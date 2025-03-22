import mediapipe as mp
import cv2
import threading
import time
import atexit

class EyeTracker:
    _instance = []
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        EyeTracker._instance.append(self)
        atexit.register(self.stop)
        
        # rough eye landmark
        self.LEFT_EYE = [33, 133]
        self.RIGHT_EYE = [362, 263]
        
        self.cap = None
        self.running = False
        self.thread = None
        
        self.look_direction = "center"  # "left", "center", "right"
        self.last_direction_change = time.time()
        self.direction_cooldown = 0.5  # seconds
        
    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.thread = threading.Thread(target=self._process_video)
        self.thread.daemon = True
        self.thread.start()
    
    def _process_video(self):
        while self.running and self.cap.isOpened():
            success, image = self.cap.read()
            if not success:
                continue
                
            # for mirror effect
            image = cv2.flip(image, 1)

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image)
            
            # draw the face mesh annotations
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            if results.multi_face_landmarks:
                self._analyze_eye_position(results.multi_face_landmarks[0])

            # cv2.imshow('MediaPipe Eye Tracking', image)
            # if cv2.waitKey(5) & 0xFF == 27:
            #     break
                
    def _analyze_eye_position(self, face_landmarks):
        """Analyze eye gaze direction based on iris position relative to eye corners"""
        
        # iris relative position
        def ratio(indices, iris_idx):
            x_values = [face_landmarks.landmark[i].x for i in indices]
            iris_x = face_landmarks.landmark[iris_idx].x
            x_min = min(x_values)
            x_max = max(x_values)
            return (iris_x - x_min) / (x_max - x_min + 1e-6)
            
        left_ratio = ratio(self.LEFT_EYE, 468)  # 468 is LEFT_IRIS
        right_ratio = ratio(self.RIGHT_EYE, 473)  # 473 is RIGHT_IRIS

        gaze_ratio = (left_ratio + right_ratio) / 2
        
        current_time = time.time()
        if current_time - self.last_direction_change >= self.direction_cooldown:
            if gaze_ratio < 0.4:
                new_direction = "left"
            elif gaze_ratio > 0.6:
                new_direction = "right"
            else:
                new_direction = "center"

            if new_direction != self.look_direction:
                self.look_direction = new_direction
                self.last_direction_change = current_time
    
    def get_direction(self):
        return self.look_direction
    
    def stop(self):
        """Stop the eye tracker and clean up resources"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.thread = None
        print("Eye tracker stopped")