from django.core.files import File
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime
from collections import deque
import os
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor
from app.alarm.models import Alarm
from django.core.files.base import ContentFile
from app.monitoring.models import VideoEvidence
from config.utils import RED_COLOR, GREEN_COLOR, YELLOW_COLOR, RESET_COLOR, BLUE_COLOR, GREY_COLOR

THEFT_DETECTION_TIME = 1
FPS = 24
FRAMES_BEFORE_AFTER = int(FPS * 0.2)
FRAMES_TO_SAVE = int(FPS * 4)
BUFFER_SIZE = int(FPS * 4)
THEFT_THRESHOLD = 55 # Diagonal (35 - 45); Frontal (60 o mas)
STOLEN_DIR = 'robberies_frames' 

mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

executor = ThreadPoolExecutor(max_workers=6)

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
    if hand_velocity > 0.1:
        score += 1
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

    shoulder_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].x,
                    pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_SHOULDER].y)
    hip_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_HIP].x,
               pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_HIP].y)
    knee_pos = (pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_KNEE].x,
                pose_landmarks.landmark[mp_holistic.PoseLandmark.LEFT_KNEE].y)

    left_hand_pos = None
    right_hand_pos = None
    suspicious_score = 0

    if left_hand_landmarks:
        left_hand_pos = (left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].x,
                         left_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].y)
        left_hand_velocity = calculate_hand_velocity(prev_left_hand, left_hand_pos, time_diff)
        suspicious_score += calculate_suspicious_score(left_hand_velocity, left_hand_pos, prev_left_hand, shoulder_pos, hip_pos, knee_pos)

    if right_hand_landmarks:
        right_hand_pos = (right_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].x,
                          right_hand_landmarks.landmark[mp_holistic.HandLandmark.WRIST].y)
        right_hand_velocity = calculate_hand_velocity(prev_right_hand, right_hand_pos, time_diff)
        suspicious_score += calculate_suspicious_score(right_hand_velocity, right_hand_pos, prev_right_hand, shoulder_pos, hip_pos, knee_pos)

    return suspicious_score, left_hand_pos, right_hand_pos

def detect_theft(frame, session):
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

    # Add current frame to buffer
    state['frame_buffer'].append((frame.copy(), current_time))

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
                print(YELLOW_COLOR + f"Acción sospechosa detectada en el frame {state['frame_count']}. Puntuación: {suspicious_score}" + RESET_COLOR)
            
            state['cumulative_score'] += suspicious_score

            if (current_time - state['suspicious_start_time']).total_seconds() >= THEFT_DETECTION_TIME and not state['theft_detected']:
                if state['cumulative_score'] >= THEFT_THRESHOLD:
                    print(RED_COLOR + f"Posible robo detectado! Puntuación acumulada: {state['cumulative_score']}")
                    print(RED_COLOR + f"Robo confirmado en el frame {state['frame_count']}." + RESET_COLOR)

                    state['theft_detected'] = True
                    state['post_theft_frame_count'] = FRAMES_TO_SAVE
                    state['theft_number'] += 1

                    executor.submit(save_theft_event, session, list(state['frame_buffer']), current_time, state['theft_number'])
                    
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
                    
                else:
                    print(BLUE_COLOR + f"Acción sospechosa descartada en el frame {state['frame_count']}. Puntuación final: {state['cumulative_score']}" + RESET_COLOR)
                state['suspicious_start_time'] = None
                state['cumulative_score'] = 0

        else:
            state['suspicious_start_time'] = None
            state['cumulative_score'] = 0
            state['theft_detected'] = False

        state['prev_left_hand'] = left_hand_pos
        state['prev_right_hand'] = right_hand_pos
        state['prev_time'] = current_time

    # Handle post-theft frame saving
    if state['theft_detected'] and state['post_theft_frame_count'] > 0:
        state['post_theft_frame_count'] -= 1
        if state['post_theft_frame_count'] == 0:
            state['theft_detected'] = False
            
    return frame

def save_theft_frames(frame_buffer, session):
    theft_folder = os.path.join(settings.MEDIA_ROOT, 'theft_evidence', f'session_{session.id}')
    os.makedirs(theft_folder, exist_ok=True)
    for i, (frame, timestamp) in enumerate(frame_buffer):
        filename = f"frame_{i:04d}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
        file_path = os.path.join(theft_folder, filename)
        cv2.imwrite(file_path, frame)
        print(GREY_COLOR + f"Frame de robo guardado: {filename}" + RESET_COLOR)
    return theft_folder

def save_theft_event(session, frame_buffer, theft_time, theft_number):
    try:
        theft_folder = save_theft_frames(frame_buffer, session)
        video_filename = f'theft_video_{theft_number}.mp4'
        video_path = os.path.join(theft_folder, video_filename)
        
        create_video_from_frames(frame_folder=theft_folder, output_video_path=video_path, fps=FPS, delete_frames=True)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"El archivo de video no existe en la ruta: {video_path}")
        
        video_evidence = VideoEvidence(session=session)
        
        with open(video_path, 'rb') as file:
            video_evidence.video_file.save(video_filename, File(file), save=True)

        print(GREEN_COLOR + f"Evento de robo guardado exitosamente" + RESET_COLOR)
        os.remove(video_path)

        Alarm.stop_alarm()

    except Exception as e:
        print(RED_COLOR + f"Error al guardar el evento de robo: {str(e)}" + RESET_COLOR)
        Alarm.stop_alarm()

def create_video_from_frames(frame_folder, output_video_path, fps, delete_frames=False):
    images = [img for img in os.listdir(frame_folder) if img.endswith(".jpg")]
    if not images:
        print(YELLOW_COLOR + "No se encontraron imágenes para crear el video." + RESET_COLOR)
        return

    frame = cv2.imread(os.path.join(frame_folder, images[0]))
    height, width, layers = frame.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for image in sorted(images):
        video.write(cv2.imread(os.path.join(frame_folder, image)))

    print(GREEN_COLOR + f"Video creado exitosamente." + RESET_COLOR)

    if delete_frames:
        for filename in sorted(os.listdir(frame_folder)):
            if filename.endswith('.jpg'):
                os.remove(os.path.join(frame_folder, filename))
        print(GREEN_COLOR + "Frames borrados exitosamente." + RESET_COLOR)

    video.release()

def cleanup():
    executor.shutdown(wait=True)    
