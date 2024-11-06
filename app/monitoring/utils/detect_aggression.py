import cv2
import numpy as np
import joblib
from collections import deque
from datetime import datetime
import os
from config.utils import GREEN_COLOR, RESET_COLOR, RED_COLOR, YELLOW_COLOR
from app.alarm.models import Alarm
from app.threat_management.models import DetectionCounter
from app.monitoring.utils.send_email import send_alert_email_video
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

current_directory = os.path.dirname(__file__)
model_path = os.path.join(current_directory, 'models/aggression_detection_model.joblib')
aggression_model = joblib.load(model_path)

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

AVG_WINDOW = 5
MIN_PROBABILITY = 0.87
THRESHOLD_AGGRESSION_POINTS = 15
VIDEO_BUFFER_SECONDS = 5

prev_frame = None
latest_odds = deque(maxlen=AVG_WINDOW)
aggression_points = 0
in_aggression = False
frame_buffer = deque(maxlen=300)

event_queue = queue.Queue()

executor = ThreadPoolExecutor(max_workers=4)

def extract_features(frame, prev_frame):
    frame_resized = cv2.resize(frame, (320, 240))
    rects, _ = hog.detectMultiScale(frame_resized, winStride=(16, 16), padding=(32, 32), scale=1.1)
    
    if prev_frame is not None:
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        caract_frame = [
            np.mean(mag),
            np.max(mag),
            len(rects),
            np.std(mag),
        ]
        return caract_frame, frame_resized
    
    return None, frame_resized

class BackgroundEventProcessor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
    
    def run(self):
        while self.running:
            try:
                event_data = event_queue.get(timeout=1)
                if event_data:
                    self._process_event(event_data)
                event_queue.task_done()
            except queue.Empty:
                continue
    
    def _process_event(self, event_data):
        frame_buffer_copy = event_data['frame_buffer'].copy()
        session = event_data['session']
        avg_probability = event_data['avg_probability']
        self._handle_alarm(session)
        executor.submit(save_video_evidence, frame_buffer_copy, session, avg_probability)
    
    def _handle_alarm(self, session):
        try:
            detection = session.detection_model
            detection_counter, created = DetectionCounter.objects.get_or_create(
                detection=detection,
                user=session.user
            )
            detection_counter.increment()
            
            alarm = Alarm.objects.filter(
                detection=detection, 
                user=session.user, 
                is_active=True
            ).first()
            
            if not alarm:
                alarm = Alarm()
                alarm = alarm.create_alarm(detection, session.user)
            if alarm:
                alarm.activate()
            else:
                print("No se pudo crear o encontrar la alarma.")
        except Exception as e:
            print(f"Error procesando alarma: {e}")
            
def save_video_evidence(frame_buffer, session, avg_probability):
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_path = f"aggression_{current_time}_prob{avg_probability:.2f}.mp4"
    
    if frame_buffer:
        height, width, _ = frame_buffer[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 12, (width, height))
        
        for frame in frame_buffer:
            out.write(frame)
        out.release()
        
        recipient_email = session.user.email
        context = {
            'session': session,
            'activation_time': current_time,
        }
        
        try:
            send_alert_email_video(
                subject=f"Evento de agresión detectado en la sesión {session.id}",
                template_name='email_content.html',
                context=context,
                recipient_list=[recipient_email],
                attachment_path=video_path,
                attachment_name=video_path
            )
        except Exception as e:
            print(f"Error al enviar el correo electrónico: {e}")
        
        try:
            os.remove(video_path)
            print(f"{GREEN_COLOR}Vídeo del evento de agresión eliminado después de enviar{RESET_COLOR}")
        except Exception as e:
            print(f"Error al eliminar el video: {e}")
            
def detect_aggression(frame, session, frame_index, fps):
    global prev_frame, latest_odds, aggression_points, in_aggression
    
    processed_frame = frame.copy()
    frame_buffer.append(frame.copy())
    characteristics, frame_resized = extract_features(frame, prev_frame)
    prev_frame = frame_resized
    
    if characteristics is not None:
        probability = aggression_model.predict_proba(np.array(characteristics).reshape(1, -1))[0][1]
        latest_odds.append(probability)
        avg_probability = np.mean(latest_odds)
        
        if avg_probability >= MIN_PROBABILITY:
            aggression_points += 1
            if not in_aggression and aggression_points >= THRESHOLD_AGGRESSION_POINTS:
                in_aggression = True
                print(f"{RED_COLOR}¡AGRESIÓN DETECTADA!{RESET_COLOR}")
                event_data = {
                    'frame_buffer': frame_buffer.copy(),
                    'session': session,
                    'avg_probability': avg_probability
                }
                event_queue.put(event_data)
                
        else:
            if in_aggression:
                aggression_points = max(0, aggression_points - 1)
                if aggression_points == 0:
                    in_aggression = False
        
        color = (0, 0, 255) if in_aggression else (0, 255, 0)
        cv2.putText(processed_frame, f"Prob: {avg_probability:.2%}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        print(f"{GREEN_COLOR}Probabilidad: {avg_probability:.2%}{RESET_COLOR}")
        
        if in_aggression:
            cv2.putText(processed_frame, "¡AGRESION DETECTADA!", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.rectangle(processed_frame, (0, 0), 
                        (processed_frame.shape[1], processed_frame.shape[0]), (0, 0, 255), 3)
            
    return processed_frame

def reset_detection_state():
    global prev_frame, latest_odds, aggression_points, in_aggression
    prev_frame = None
    latest_odds.clear()
    aggression_points = 0
    in_aggression = False
    print(f"{YELLOW_COLOR}Estado de detección de agresión reiniciado{RESET_COLOR}")
    
background_processor = BackgroundEventProcessor()
background_processor.start()