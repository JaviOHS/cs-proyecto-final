from datetime import datetime
import cv2
import numpy as np
import joblib
import os
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from app.alarm.models import Alarm
from django.conf import settings
from app.monitoring.utils.send_email import send_alert_email_video
from config.utils import RED_COLOR, GREEN_COLOR, RESET_COLOR, YELLOW_COLOR
from app.threat_management.models import DetectionCounter

current_directory = os.path.dirname(__file__)
model_path = os.path.join(current_directory, 'models/aggression_detection_model.joblib')

model_loaded = joblib.load(model_path)

NO_AGGRESSION_FRAMES_THRESHOLD = 35
AGGRESSION_FRAMES_THRESHOLD = 15 
detection_interval = 5

class AggressionDetector:
    def __init__(self):
        self.aggression_event_active = False
        self.frames_without_aggression = 0
        self.aggression_frames = deque(maxlen=300)
        self.prev_frame = None
        self.frame_count = 0
        self.current_event_id = None
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.fps = 12  
    
    def set_fps(self, fps):
        """Establecer los cuadros por segundo para ajustar los umbrales."""
        self.fps = fps
        self.no_aggression_frames_threshold = int(NO_AGGRESSION_FRAMES_THRESHOLD * (fps / 12))
        
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

    def process_detection(self, frame, session, frame_index):
        features, frame_resized = self.extract_features(frame)
        self.prev_frame = frame_resized

        if features is not None:
            prediction = model_loaded.predict(np.array(features).reshape(1, -1))

            if prediction[0] == 1:
                self.aggression_frames.append(frame)

                
                if not self.aggression_event_active:
                    self.start_aggression_event(session, frame_index)
                
                
                self.frames_without_aggression = 0

            else:
                
                if self.aggression_event_active:
                    self.frames_without_aggression += 1
                    print(f"{YELLOW_COLOR}Frame {frame_index} - Frames sin agresión: {self.frames_without_aggression}/{self.no_aggression_frames_threshold}{RESET_COLOR}")

                    if self.frames_without_aggression >= self.no_aggression_frames_threshold:
                        self.end_aggression_event(session)
                else:
                    self.aggression_frames.clear()

    def start_aggression_event(self, session, frame_index):
        self.aggression_event_active = True
        self.current_event_id = f"event_{session.id}_{frame_index}"
        print(RED_COLOR + f"Se inició el evento de agresión. ID: {self.current_event_id}, Frame: {frame_index}" + RESET_COLOR)
        
        detection = session.detection_model
        detection_counter, created = DetectionCounter.objects.get_or_create(
            detection=detection,
            user=session.user
        )
        detection_counter.increment()
        
        alarm = Alarm.objects.filter(detection=detection, user=session.user, is_active=True).first()
        if not alarm:
            alarm = Alarm()
            alarm = alarm.create_alarm(detection, session.user)
        if alarm:
            self.executor.submit(alarm.activate)
        else:
            print("No se pudo crear o encontrar la alarma.")

    def end_aggression_event(self, session):
        if self.aggression_event_active:
            print(RED_COLOR + f"Evento de agresión finalizado. ID: {self.current_event_id}" + RESET_COLOR)
            Alarm.stop_alarm()
            self.executor.submit(self.save_aggression_event, list(self.aggression_frames), session, self.current_event_id)
            self.reset_state()

    def detect_aggression(self, frame, session, frame_index, fps):
        if self.fps != fps:
            self.set_fps(fps)


        print(f"{YELLOW_COLOR}Procesando detección de agresión en el frame {frame_index}{RESET_COLOR}")
        self.executor.submit(self.process_detection, frame.copy(), session, frame_index)
        return frame

    def reset_state(self):
        self.aggression_event_active = False
        self.frames_without_aggression = 0
        self.aggression_frames.clear()
        self.current_event_id = None

    @staticmethod
    def save_aggression_event(frames, session, event_id):
        video_path = f"event_{event_id}.mp4"
        
        height, width, layers = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        video = cv2.VideoWriter(video_path, fourcc, 12, (width, height))
        for frame in frames:
            video.write(frame)
        video.release()
        
        print(GREEN_COLOR + f"Vídeo del evento de agresión guardado en {video_path}" + RESET_COLOR)
        
        recipient_email = session.user.email
        current_time = datetime.now()
        context = {
            'session': session,
            'activation_time': current_time.strftime("%d/%m/%Y %H:%M:%S"),
            'event_id': event_id,
            'is_aggression': True,
        }
        
        try:
            send_alert_email_video(
                subject=f"Evento de agresión detectado en la sesión {session.id}",
                template_name='email_content.html',
                context=context,
                recipient_list=[recipient_email],
                attachment_path=video_path,
                attachment_name=f"event_{event_id}.mp4"
            )
        except Exception as e:
            print(f"Error al enviar el correo electrónico: {e}")
        
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(GREEN_COLOR + f"Vídeo del evento {event_id} eliminado después de enviarlo." + RESET_COLOR)
            else:
                print(f"El archivo de video {video_path} no se encontró para eliminar.")
        except Exception as e:
            print(f"Error al intentar eliminar el archivo de video: {e}")


detector = AggressionDetector()


def detect_aggression(frame, session, frame_index, fps):
    return detector.detect_aggression(frame, session, frame_index, fps)
