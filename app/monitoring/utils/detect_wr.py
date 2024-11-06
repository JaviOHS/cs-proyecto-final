import boto3
import os
import cv2
import time
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor
from app.alarm.models import Alarm
from app.monitoring.utils.send_email import send_alert_email_video
from app.threat_management.models import DetectionCounter
from config.utils import GREEN_COLOR, RESET_COLOR, RED_COLOR, YELLOW_COLOR
import numpy as np
import queue
import threading

max_no_detection_frames = 5
detection_interval = 60

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

TOY_COLORS = {
    'bright_orange': ([5, 50, 50], [15, 255, 255]),
    'bright_blue': ([100, 150, 100], [130, 255, 255]),
    'bright_green': ([45, 150, 100], [75, 255, 255]),
    'bright_red': ([0, 150, 100], [5, 255, 255]),
    'bright_yellow': ([20, 150, 100], [30, 255, 255])
}

VALIDATION_CONFIG = {
    'max_toy_color_ratio': 0.3,
    'min_metallic_ratio': 0.15,
    'context_labels_toy': [
        'Toy', 'Game', 'Play', 'Child', 'Kids', 'Plastic',
        'Entertainment', 'Recreation', 'Costume', 'Party'
    ],
    'context_labels_real': [
        'Military', 'Police', 'Combat', 'Tactical', 'Security',
        'Steel', 'Metal', 'Ammunition', 'Magazine'
    ]
}

class WeaponValidator:
    def __init__(self):
        self.metallic_colors_hsv = {
            'dark_gray': ([0, 0, 40], [180, 30, 140]),
            'metallic': ([0, 0, 140], [180, 30, 220]),
            'black': ([0, 0, 0], [180, 30, 40])
        }
    
    def is_valid_weapon(self, frame, bbox, detected_labels):
        try:
            height, width = frame.shape[:2]
            x1 = int(bbox['Left'] * width)
            y1 = int(bbox['Top'] * height)
            x2 = int((bbox['Left'] + bbox['Width']) * width)
            y2 = int((bbox['Top'] + bbox['Height']) * height)
            
            weapon_region = frame[y1:y2, x1:x2]
            if weapon_region.size == 0:
                return False, 0, "Región de detección inválida"
            hsv_region = cv2.cvtColor(weapon_region, cv2.COLOR_BGR2HSV)
            toy_color_ratio = self._calculate_toy_color_ratio(hsv_region)
            if toy_color_ratio > VALIDATION_CONFIG['max_toy_color_ratio']:
                return False, 0.4, f"Alto porcentaje de colores típicos de juguete ({toy_color_ratio:.2%})"
            metallic_ratio = self._calculate_metallic_ratio(hsv_region)
            if metallic_ratio < VALIDATION_CONFIG['min_metallic_ratio']:
                return False, 0.5, f"Bajo porcentaje de colores metálicos ({metallic_ratio:.2%})"
            context_score = self._analyze_context(detected_labels)
            if context_score < 0:
                return False, 0.6, "Contexto sugiere juguete"
            if self._has_orange_tip(weapon_region):
                return False, 0.2, "Detectada punta naranja característico de juguete"
            confidence = min(0.95, (metallic_ratio + (1 - toy_color_ratio) + context_score) / 3)
            return True, confidence, "Validación exitosa"

        except Exception as e:
            print(f"{RED_COLOR}Error en la validación: {e}{RESET_COLOR}")
            return False, 0, f"Error en validación: {str(e)}"

    def _calculate_toy_color_ratio(self, hsv_image):
        toy_mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
        for color_range in TOY_COLORS.values():
            lower, upper = np.array(color_range[0]), np.array(color_range[1])
            mask = cv2.inRange(hsv_image, lower, upper)
            toy_mask = cv2.bitwise_or(toy_mask, mask)
        return np.count_nonzero(toy_mask) / (hsv_image.shape[0] * hsv_image.shape[1])

    def _calculate_metallic_ratio(self, hsv_image):
        metallic_mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
        for color_range in self.metallic_colors_hsv.values():
            lower, upper = np.array(color_range[0]), np.array(color_range[1])
            mask = cv2.inRange(hsv_image, lower, upper)
            metallic_mask = cv2.bitwise_or(metallic_mask, mask)
        return np.count_nonzero(metallic_mask) / (hsv_image.shape[0] * hsv_image.shape[1])

    def _has_orange_tip(self, weapon_region):
        height, width = weapon_region.shape[:2]
        tip_region = weapon_region[0:height, width-int(width*0.2):width]
        hsv_tip = cv2.cvtColor(tip_region, cv2.COLOR_BGR2HSV)
        
        lower_orange, upper_orange = np.array(TOY_COLORS['bright_orange'][0]), np.array(TOY_COLORS['bright_orange'][1])
        orange_mask = cv2.inRange(hsv_tip, lower_orange, upper_orange)
        
        orange_ratio = np.count_nonzero(orange_mask) / (tip_region.shape[0] * tip_region.shape[1])
        return orange_ratio > 0.3

    def _analyze_context(self, detected_labels):
        toy_context_count = sum(1 for label in detected_labels if label[0] in VALIDATION_CONFIG['context_labels_toy'])
        real_context_count = sum(1 for label in detected_labels if label[0] in VALIDATION_CONFIG['context_labels_real'])
        
        return real_context_count - toy_context_count

class DetectionState:
    def __init__(self):
        self.frames_buffer = []
        self.is_detecting = False
        self.last_detection_time = time.time()
        self.event_start_time = None
        self.frames_after_detection = 0  # Contador para frames después de la última detección

detection_state = DetectionState()

def detect_objects_in_frame(frame, session, frame_index, fps):
    weapon_validator = WeaponValidator()
    
    _, jpeg_image = cv2.imencode('.jpg', frame)
    image_bytes = jpeg_image.tobytes()

    try:
        response = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=20,
            MinConfidence=60
        )
        
        detected_weapons = []
        for label in response['Labels']:
            if label['Name'] in ['Knife', 'Pistol', 'Weapon', 'Gun', 'Firearm', 'Rifle', 'Shotgun', 'Revolver', 'Handgun']:
                if 'Instances' in label and label['Instances']:
                    for instance in label['Instances']:
                        is_valid, confidence, reason = weapon_validator.is_valid_weapon(
                            frame, 
                            instance['BoundingBox'],
                            [(l['Name'], l['Confidence']) for l in response['Labels']]
                        )
                        
                        if is_valid:
                            detected_weapons.append((
                                label['Name'],
                                confidence * label['Confidence'],
                                instance['BoundingBox']
                            ))
                        else:
                            print(f"{YELLOW_COLOR}Detección descartada: {reason}{RESET_COLOR}")

        if detected_weapons:
            process_detection(frame, detected_weapons, session, frame_index)
            frame = draw_validated_detections(frame, detected_weapons)
            
        elif detection_state.is_detecting:
            # No se detectó objeto pero estamos en período de gracia
            detection_state.frames_after_detection += 1
            detection_state.frames_buffer.append(current_frame)  # Añadir frame no detectado
            
            # Verificar si debemos terminar la grabación
            if detection_state.frames_after_detection >= max_no_detection_frames:
                save_video_segment(detection_state.frames_buffer, detection_state.event_start_time, session, detected_items)
                detection_state.is_detecting = False
                detection_state.frames_buffer = []

        detection_state.frames_buffer.append((frame.copy(), time.time()))
        
        return frame

    except Exception as e:
        print(f"{RED_COLOR}Error en la detección: {e}{RESET_COLOR}")
        return frame
    
def draw_validated_detections(frame, detected_weapons):
    for weapon_name, confidence, bbox in detected_weapons:
        height, width = frame.shape[:2]
        x1 = int(bbox['Left'] * width)
        y1 = int(bbox['Top'] * height)
        x2 = int((bbox['Left'] + bbox['Width']) * width)
        y2 = int((bbox['Top'] + bbox['Height']) * height)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"{weapon_name}: {confidence:.1f}%"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return frame

executor = ThreadPoolExecutor(max_workers=4)
event_queue = queue.Queue()

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
        session = event_data['session']
        video_path = event_data['video_path']
        detected_items = event_data['detected_items']
        executor.submit(send_email_with_video, session, video_path, detected_items)

background_processor = BackgroundEventProcessor()
background_processor.start()

def send_email_with_video(session, video_path, detected_items):
    recipient_email = session.user.email
    weapons_info = ', '.join(item[0] for item in detected_items)
    context = {
        'session': session,
        'weapons_info': weapons_info,
        'activation_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'is_weapon': True
    }
    
    try:
        send_alert_email_video(
            subject=f'Detección de arma en la sesión {session.id}',
            template_name='email_content.html',
            context=context,
            recipient_list=[recipient_email],
            attachment_path=video_path,
            attachment_name=os.path.basename(video_path)
        )
        os.remove(video_path)
        print(f"{GREEN_COLOR}Video {video_path} eliminado después de enviar el correo.{RESET_COLOR}")
    except Exception as e:
        print(f"{RED_COLOR}Error al enviar el correo: {e}{RESET_COLOR}")

def process_detection(frame, detected_items, session, frame_index):
    if not detection_state.is_detecting:
        detection_state.is_detecting = True
        detection_state.last_detection_time = time.time()
        detection_state.event_start_time = time.time()
        print(f"{YELLOW_COLOR}Detección en el fotograma {frame_index}: objeto de interés detectado.{RESET_COLOR}")
        send_alert(detected_items, session)
    detection_state.last_detection_time = time.time()

def save_video_segment(frames, start_time, session, detected_items):
    if not frames:  # Verificar que hay frames para guardar
        return

    video_filename = f"{start_time:.2f}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = os.path.join(settings.BASE_DIR, video_filename)
    height, width, _ = frames[0][0].shape
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 4, (width, height))

    for frame, _ in frames:
        out.write(frame)
    out.release()

    event_data = {
        'session': session,
        'video_path': video_path,
        'detected_items': detected_items
    }
    event_queue.put(event_data)
       
def send_alert(detected_items, session):
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
                
    alert_message = f"{YELLOW_COLOR}¡Alerta! Detección de: {', '.join(item[0] for item in detected_items)}{RESET_COLOR}"
    print(alert_message)
    return alert_message