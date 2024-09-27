import cv2
import numpy as np
import joblib
import os
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from app.alarm.models import Alarm
from django.conf import settings
from config.utils import RED_COLOR, GREEN_COLOR, RESET_COLOR, YELLOW_COLOR

current_directory = os.path.dirname(__file__)
model_path = os.path.join(current_directory, 'aggression_detection_model.joblib')

model_loaded = joblib.load(model_path)

NO_AGGRESSION_FRAMES_THRESHOLD = 45
AGGRESSION_FRAMES_THRESHOLD = 30

class AggressionDetector:
    def __init__(self):
        self.aggression_event_active = False
        self.frames_without_aggression = 0
        self.frames_with_aggression = 0
        self.aggression_frames = deque(maxlen=300)
        self.prev_frame = None
        self.frame_count = 0
        self.current_event_id = None
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.executor = ThreadPoolExecutor(max_workers=4)

    def extract_features(self, frame):
        frame_resized = cv2.resize(frame, (320, 240))
        
        rects, _ = self.hog.detectMultiScale(frame_resized, winStride=(16, 16), padding=(32, 32), scale=1.1)
        
        if self.prev_frame is not None:
            prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            features_frame = [
                np.mean(mag),
                np.max(mag),
                len(rects),
                np.std(mag),
            ]
            return features_frame, frame_resized
        
        return None, frame_resized

    def process_detection(self, frame, session):
        features, frame_resized = self.extract_features(frame)
        self.prev_frame = frame_resized
        
        if features is not None:
            prediction = model_loaded.predict(np.array(features).reshape(1, -1))

            if prediction[0] == 1:
                self.aggression_frames.append(frame)
                self.frames_with_aggression += 1
                self.frames_without_aggression = 0
                
                if not self.aggression_event_active and self.frames_with_aggression >= AGGRESSION_FRAMES_THRESHOLD:
                    self.start_aggression_event(session)
            else:
                if self.aggression_event_active:
                    self.frames_without_aggression += 1
                    if self.frames_without_aggression >= NO_AGGRESSION_FRAMES_THRESHOLD:
                        self.end_aggression_event(session)
                else:
                    self.aggression_frames.clear()

    def start_aggression_event(self, session):
        self.aggression_event_active = True
        self.current_event_id = f"event_{session.id}_{self.frame_count}"
        print(RED_COLOR + f"Se inició el evento de agresión. ID: {self.current_event_id}" + RESET_COLOR)
        
        alarm = Alarm.objects.filter(
            detection=session.detection_models.first(),
            user=session.user,
            is_active=True
        ).first() 
        
        if alarm:
            print(GREEN_COLOR + f"Alarma activada para el modelo de detección {alarm.detection.name}" + RESET_COLOR)
            alarm.activate()
        else:
            print(YELLOW_COLOR + "No se encontró una alarma personalizada para el modelo de detección. Se ha activado la alarma por defecto." + RESET_COLOR)
            default_alarm = Alarm()
            default_alarm.play_default_alarm()

    def end_aggression_event(self, session):
        if self.aggression_event_active:
            print(RED_COLOR + f"Evento de agresión finalizado. ID: {self.current_event_id}" + RESET_COLOR)
            Alarm.stop_alarm()
            self.executor.submit(self.save_aggression_event, list(self.aggression_frames), session, self.current_event_id)
            self.reset_state()

    def reset_state(self):
        self.aggression_event_active = False
        self.frames_with_aggression = 0
        self.frames_without_aggression = 0
        self.aggression_frames.clear()
        self.current_event_id = None

    def detect_aggression(self, frame, session):
        if self.frame_count % 5 == 0:
            self.executor.submit(self.process_detection, frame.copy(), session)
        self.frame_count += 1
        return frame

    @staticmethod
    def save_aggression_event(frames, session, event_id):
        violent_folder = os.path.join(settings.MEDIA_ROOT, 'violent_events', f'session_{session.id}')
        
        if not os.path.exists(violent_folder):
            os.makedirs(violent_folder)
        
        existing_events = [f for f in os.listdir(violent_folder) if f.startswith('event_') and f.endswith('.mp4')]
        if existing_events:
            last_event_num = max([int(f.split('_')[1].split('.')[0]) for f in existing_events])
            next_event_num = last_event_num + 1
        else:
            next_event_num = 1
        
        video_path = os.path.join(violent_folder, f"event_{next_event_num}.mp4")
        
        height, width, layers = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        video = cv2.VideoWriter(video_path, fourcc, 12, (width, height))
        
        for frame in frames:
            video.write(frame)
        
        video.release()
        
        print(GREEN_COLOR + f"Vídeo del evento de agresión guardado en {video_path}" + RESET_COLOR)

detector = AggressionDetector()

def detect_aggression(frame, session):
    return detector.detect_aggression(frame, session)