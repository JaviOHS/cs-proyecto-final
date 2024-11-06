import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from collections import deque
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from app.alarm.models import Alarm
from app.threat_management.models import DetectionCounter
from app.monitoring.utils.send_email import send_alert_email_video
from config.utils import RED_COLOR, GREEN_COLOR, YELLOW_COLOR, RESET_COLOR, BLUE_COLOR

THEFT_DETECTION_TIME = 2
THEFT_THRESHOLD = 20
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
event_queue = queue.Queue()
executor = ThreadPoolExecutor(max_workers=4)

def calculate_hand_velocity(prev_hand_pos, current_hand_pos, time_diff):
    if prev_hand_pos is None or current_hand_pos is None:
        return 0
    distance = np.sqrt((current_hand_pos[0] - prev_hand_pos[0])**2 + (current_hand_pos[1] - prev_hand_pos[1])**2)
    return distance / time_diff if time_diff > 0 else 0

def is_hand_near_body_area(hand_pos, shoulder_pos, hip_pos, knee_pos):
    if hand_pos is None or shoulder_pos is None or knee_pos is None:
        return False
    return shoulder_pos[1] < hand_pos[1] < knee_pos[1]

def is_hand_near_torso(hand_pos, shoulder_pos, hip_pos):
    if hand_pos is None or shoulder_pos is None or hip_pos is None:
        return False
    return (shoulder_pos[1] < hand_pos[1] < hip_pos[1]) and \
           (min(shoulder_pos[0], hip_pos[0]) < hand_pos[0] < max(shoulder_pos[0], hip_pos[0]))
           
def is_hand_near_legs(hand_pos, hip_pos, knee_pos):
    if hand_pos is None or hip_pos is None or knee_pos is None:
        return False
    return (hip_pos[1] < hand_pos[1] < knee_pos[1]) and \
        (min(hip_pos[0], knee_pos[0]) < hand_pos[0] < max(hip_pos[0], knee_pos[0]))
           
def calculate_suspicious_score(hand_velocity, hand_pos, prev_hand_pos, shoulder_pos, hip_pos, knee_pos):
    score = 0
    if hand_pos is None or prev_hand_pos is None:
        return score
    if hand_velocity > 0.2:
        score += 2
    if is_hand_near_body_area(hand_pos, shoulder_pos, hip_pos, knee_pos):
        score += 3
        if not is_hand_near_body_area(prev_hand_pos, shoulder_pos, hip_pos, knee_pos):
            score += 1
        if is_hand_near_torso(hand_pos, shoulder_pos, hip_pos) or is_hand_near_legs(hand_pos, hip_pos, knee_pos):
            score += 3
    return score

def detect_suspicious_action(pose_landmarks, left_hand_landmarks, right_hand_landmarks, prev_left_hand, prev_right_hand, time_diff):
    if pose_landmarks is None:
        return 0, None, None

    shoulder_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].x, pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].y)
    hip_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_HIP].x, pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_HIP].y)
    knee_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_KNEE].x, pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_KNEE].y)

    left_hand_pos = None
    right_hand_pos = None
    suspicious_score = 0

    if left_hand_landmarks:
        left_hand_pos = (left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].x, left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].y)
        left_hand_velocity = calculate_hand_velocity(prev_left_hand, left_hand_pos, time_diff)
        suspicious_score += calculate_suspicious_score(left_hand_velocity, left_hand_pos, prev_left_hand, shoulder_pos, hip_pos, knee_pos)

    if right_hand_landmarks:
        right_hand_pos = (right_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].x, right_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].y)
        right_hand_velocity = calculate_hand_velocity(prev_right_hand, right_hand_pos, time_diff)
        suspicious_score += calculate_suspicious_score(right_hand_velocity, right_hand_pos, prev_right_hand, shoulder_pos, hip_pos, knee_pos)

    return suspicious_score, left_hand_pos, right_hand_pos

def detect_theft(frame, session, frame_index, fps):
    FRAMES_TO_SAVE = int(fps * 6)
    BUFFER_SIZE = int(fps * 6)

    if not hasattr(session, 'theft_detection_state'):
        session.theft_detection_state = {
            'frame_count': 0,
            'frame_buffer': deque(maxlen=BUFFER_SIZE),
            'suspicious_start_time': None,
            'cumulative_score': 0,
            'theft_detected': False,
            'post_theft_frame_count': 0,
            'prev_time': None,
            'prev_left_hand': None,
            'prev_right_hand': None,
            'theft_number': 0
        }

    state = session.theft_detection_state
    state['frame_count'] += 1
    current_time = datetime.now()
    results = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    state['frame_buffer'].append((frame.copy(), datetime.now()))

    if results.pose_landmarks:
        time_diff = (current_time - state['prev_time']).total_seconds() if state['prev_time'] else 0
        suspicious_score, left_hand_pos, right_hand_pos = detect_suspicious_action(
            results.pose_landmarks,
            results.left_hand_landmarks,
            results.right_hand_landmarks,
            state['prev_left_hand'],
            state['prev_right_hand'],
            time_diff
        )

        if suspicious_score > 0:
            if state['suspicious_start_time'] is None:
                state['suspicious_start_time'] = current_time
                print(f"{YELLOW_COLOR}Acción sospechosa. Puntuación: {suspicious_score}{RESET_COLOR}")
            
            state['cumulative_score'] += suspicious_score

            if (current_time - state['suspicious_start_time']).total_seconds() >= THEFT_DETECTION_TIME and not state['theft_detected']:
                if state['cumulative_score'] >= THEFT_THRESHOLD:
                    print(f"{RED_COLOR}Posible robo detectado. Puntuación acumulada: {state['cumulative_score']}{RESET_COLOR}")
                    state['theft_detected'] = True
                    state['post_theft_frame_count'] = FRAMES_TO_SAVE
                    state['theft_number'] += 1

                    event_data = {
                        'frame_buffer': list(state['frame_buffer']),
                        'session': session,
                        'theft_time': current_time,
                        'theft_number': state['theft_number'],
                        'fps': fps
                    }
                    event_queue.put(event_data)
                    
                else:
                    print(f"{BLUE_COLOR}Acción sospechosa descartada en el frame {state['frame_count']}. Puntuación final: {state['cumulative_score']}{RESET_COLOR}")
                state['suspicious_start_time'] = None
                state['cumulative_score'] = 0
        else:
            state['suspicious_start_time'] = None
            state['cumulative_score'] = 0
            state['theft_detected'] = False

        state['prev_left_hand'] = left_hand_pos
        state['prev_right_hand'] = right_hand_pos
        state['prev_time'] = current_time

    if state['theft_detected'] and state['post_theft_frame_count'] > 0:
        state['post_theft_frame_count'] -= 1
        if state['post_theft_frame_count'] == 0:
            state['theft_detected'] = False
            state['frame_buffer'].clear()
            
    return frame

class BackgroundEventProcessor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
    
    def run(self):
        while self.running:
            try:
                event_data = event_queue.get(timeout=1)
                if event_data:
                    self._process_theft_event(event_data)
                event_queue.task_done()
            except queue.Empty:
                continue
    
    def _process_theft_event(self, event_data):
        try:
            frame_buffer = event_data['frame_buffer']
            session = event_data['session']
            theft_time = event_data['theft_time']
            theft_number = event_data['theft_number']
            fps = event_data['fps']
            self._handle_alarm(session)

            executor.submit(
                save_theft_event,
                session,
                frame_buffer,
                theft_time,
                theft_number,
                fps
            )
        except Exception as e:
            print(f"{RED_COLOR}Error procesando evento de robo: {str(e)}{RESET_COLOR}")
    
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

def save_theft_event(session, frame_buffer, theft_time, theft_number, fps):
    try:
        video_filename = f'theft_video_{theft_number}.mp4'
        video_path = os.path.join(settings.BASE_DIR, video_filename)
        
        create_video_from_frames(frame_buffer, video_path, fps)
        
        recipient_email = session.user.email
        current_time = datetime.now()
        context = {
            'session': session,
            'activation_time': current_time.strftime("%d/%m/%Y %H:%M:%S"),
            'theft_time': theft_time.strftime("%d/%m/%Y %H:%M:%S"),
            'theft_number': theft_number,
            'is_theft': True
        }
        
        send_alert_email_video(
            subject="Alerta de Robo Detectado",
            template_name="email_content.html",
            context=context,
            recipient_list=[recipient_email],
            attachment_path=video_path,
            attachment_name=video_filename
        )
        
        os.remove(video_path)
        print(f"{GREEN_COLOR}Video de evento eliminado después de enviar{RESET_COLOR}")
    except Exception as e:
        print(f"{RED_COLOR}Error al guardar el evento de robo: {str(e)}{RESET_COLOR}")

def create_video_from_frames(frame_buffer, output_video_path, fps):
    if not frame_buffer:
        print(f"{YELLOW_COLOR}No hay fotogramas en el buffer para crear el video.{RESET_COLOR}")
        return
    frame_height, frame_width, _ = frame_buffer[0][0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
    for frame, _ in frame_buffer:
        video_writer.write(frame)
    video_writer.release()
    
def cleanup():
    executor.shutdown(wait=True)    

background_processor = BackgroundEventProcessor()
background_processor.start()

def cleanup():
    background_processor.running = False
    background_processor.join()
    executor.shutdown(wait=True)