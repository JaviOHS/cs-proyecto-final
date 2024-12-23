import os
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
import cv2
import numpy as np
from datetime import datetime
from collections import deque
from config.utils import GREEN_COLOR, RESET_COLOR, RED_COLOR
from app.monitoring.utils.send_email import send_alert_email_video
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from app.alarm.models import Alarm
from app.threat_management.models import DetectionCounter
import threading
from django.db import transaction

current_directory = os.path.dirname(__file__)
options = vision.ObjectDetectorOptions(
    base_options=BaseOptions(model_asset_path=os.path.join(current_directory, "models/object_detection.tflite")),
    max_results=5,
    score_threshold=0.2,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.ObjectDetector.create_from_options(options)

frames_interval = 4  
min_frames_stationary = 20  
max_missing_frames = 5  
object_history = {}  
min_frames_to_confirm_new = 30  
size_change_threshold = 0.3  
max_distance = 50  

BUFFER_SIZE = 100
frame_buffer = deque(maxlen=BUFFER_SIZE)
executor = ThreadPoolExecutor(max_workers=6)

def calculate_iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    xi1, yi1 = max(x1, x2), max(y1, y2)
    xi2, yi2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area
    iou = inter_area / union_area if union_area > 0 else 0
    return iou

def calculate_center(bbox):
    x, y, w, h = bbox
    return (x + w / 2, y + h / 2)

def average_bounding_boxes(old_bbox, new_bbox, alpha=0.5):
    x1, y1, w1, h1 = old_bbox
    x2, y2, w2, h2 = new_bbox
    return (
        int(alpha * x1 + (1 - alpha) * x2),
        int(alpha * y1 + (1 - alpha) * y2),
        int(alpha * w1 + (1 - alpha) * w2),
        int(alpha * h1 + (1 - alpha) * h2)
    )

def is_on_ground(bbox, frame_height, ground_ratio=0.4):
    _, y, _, h = bbox
    bottom_y = y + h
    ground_threshold = frame_height * (1 - ground_ratio)
    object_ground_threshold = h * 0.2
    return bottom_y >= ground_threshold + object_ground_threshold

def detect_drop_items(frame, session, frame_index, fps):
    global object_history
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    frame_timestamp_ms = int(1000 * frame_index / fps)
    
    if hasattr(detect_drop_items, 'last_timestamp') and frame_timestamp_ms <= detect_drop_items.last_timestamp:
        frame_timestamp_ms = detect_drop_items.last_timestamp + 1
    
    detect_drop_items.last_timestamp = frame_timestamp_ms

    detection_result = detector.detect_for_video(frame_rgb, frame_timestamp_ms)
    
    current_objects = {}
    for detection in detection_result.detections:
        bbox = detection.bounding_box
        category = detection.categories[0].category_name
        if category not in ["person", "chair", "couch", "bed", "dining table", "toilet", "tv", "scissors", "dog", "cat", "suitcase", "refrigerator", "cake", "cow"]:
            current_objects[category] = (bbox.origin_x, bbox.origin_y, bbox.width, bbox.height)

    frame_buffer.append((frame.copy(), datetime.now()))
    new_detections = False

    # Calcula la altura para la línea del suelo
    ground_threshold = frame.shape[0] * (1 - 0.4)  # Suponiendo que el ground_ratio es 0.4
    cv2.line(frame, (0, int(ground_threshold)), (frame.shape[1], int(ground_threshold)), (255, 0, 0), 2)  # Dibuja la línea del suelo

    for category, bbox in current_objects.items():
        if category not in object_history:
            object_history[category] = {
                'bbox': bbox, 
                'frames_stationary': 0, 
                'missing_frames': 0, 
                'is_new': True,
                'alarm_activated': False
            }
        else:
            iou = calculate_iou(object_history[category]['bbox'], bbox)
            center_old = calculate_center(object_history[category]['bbox'])
            center_new = calculate_center(bbox)
            distance = np.linalg.norm(np.array(center_old) - np.array(center_new))

            if (iou > 0.6 or distance < max_distance):
                old_w, old_h = object_history[category]['bbox'][2], object_history[category]['bbox'][3]
                new_w, new_h = bbox[2], bbox[3]

                if abs(new_w - old_w) / old_w < size_change_threshold and abs(new_h - old_h) / old_h < size_change_threshold:
                    object_history[category]['frames_stationary'] += 1
                    object_history[category]['bbox'] = average_bounding_boxes(object_history[category]['bbox'], bbox)
                    object_history[category]['missing_frames'] = 0
            else:
                object_history[category]['bbox'] = bbox
                object_history[category]['frames_stationary'] = 0

    for category, info in object_history.items():
        if info['frames_stationary'] >= min_frames_stationary and is_on_ground(info['bbox'], frame.shape[0]):
            status = "NUEVO" if info['is_new'] else "CAÍDO"
            x, y, w, h = info['bbox']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, f"{status}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if info['is_new'] and info['frames_stationary'] >= min_frames_to_confirm_new:
                executor.submit(save_and_send_video, session, list(frame_buffer), category, fps)
                info['is_new'] = False
            if not info['alarm_activated']:
                new_detections = True
                info['alarm_activated'] = True

        if category not in current_objects:
            info['missing_frames'] += 1
            if info['missing_frames'] > max_missing_frames:
                info['alarm_activated'] = False
                info['is_new'] = True

    object_history = {k: v for k, v in object_history.items() if v['missing_frames'] <= max_missing_frames}
    if new_detections:
        threading.Thread(target=handle_new_detections, args=(session,)).start()

    return frame

def handle_new_detections(session):
    with transaction.atomic():
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
            executor.submit(alarm.activate)
        else:
            print("No se pudo crear o encontrar la alarma.")
                      
def save_and_send_video(session, frame_buffer, category, fps):
    try:
        video_filename = f'dropped_item_{category}.mp4'
        video_path = os.path.join(settings.BASE_DIR, video_filename)
        
        create_video_from_frames(frame_buffer, video_path, fps)
        
        is_drop = True
        recipient_email = session.user.email
        current_time = datetime.now()
        context = {
            'session': session,
            'activation_time': current_time.strftime("%d/%m/%Y %H:%M:%S"),
            'category': category,
            'is_drop': is_drop
        }
        
        send_alert_email_video(
            subject=f"Alerta: Objeto Caído Detectado - {category}",
            template_name="email_content.html",
            context=context,
            recipient_list=[recipient_email],
            attachment_path=video_path,
            attachment_name=video_filename
        )
        
        os.remove(video_path)
        print(f"{GREEN_COLOR}Video {video_filename} eliminado después de enviar.{RESET_COLOR}")

    except Exception as e:
        print(f"{RED_COLOR}Error al guardar el evento de objeto caído: {str(e)}{RESET_COLOR}")

def create_video_from_frames(frame_buffer, output_video_path, fps):
    if not frame_buffer:
        return
    height, width = frame_buffer[0][0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    for frame, _ in frame_buffer:
        out.write(frame)
    out.release()
