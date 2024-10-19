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

executor = ThreadPoolExecutor(max_workers=4)

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

max_no_detection_frames = 30
detection_interval = 60  

class DetectionState:
    def __init__(self):
        self.frames_buffer = []
        self.is_detecting = False
        self.last_detection_time = time.time()
        self.event_start_time = None

detection_state = DetectionState()

def detect_objects_in_frame(frame, session, frame_index, fps):
    _, jpeg_image = cv2.imencode('.jpg', frame)
    image_bytes = jpeg_image.tobytes()

    try:
        response = rekognition.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=75
        )

        detected_items = [
            (label['Name'], label['Confidence'])
            for label in response['Labels']
            if label['Name'] in ['Knife', 'Pistol', 'Weapon', 'Gun', 'Firearm', 'Rifle', 'Shotgun', 'Revolver', 'Handgun']
        ]

        if detected_items:
            process_detection(frame, detected_items, session, frame_index)
        elif detection_state.is_detecting:
            if time.time() - detection_state.last_detection_time > max_no_detection_frames * detection_interval / fps:
                save_video_segment(detection_state.frames_buffer, detection_state.event_start_time, session, [])
                detection_state.is_detecting = False
                detection_state.frames_buffer = []

        # Siempre añadimos el frame actual al buffer
        detection_state.frames_buffer.append((frame.copy(), time.time()))
        
        # Limitamos el tamaño del buffer
        max_buffer_size = int(fps * 10)  # Por ejemplo, 10 segundos de video
        if len(detection_state.frames_buffer) > max_buffer_size:
            detection_state.frames_buffer.pop(0)

        return draw_labels_on_frame(frame, detected_items)

    except Exception as e:
        print(f"{RED_COLOR}Error al llamar a Rekognition: {e}{RESET_COLOR}")
        return frame
    
def process_detection(frame, detected_items, session, frame_index):
    if not detection_state.is_detecting:
        detection_state.is_detecting = True
        detection_state.last_detection_time = time.time()
        detection_state.event_start_time = time.time()
        print(f"{YELLOW_COLOR}Detección en el fotograma {frame_index}: Se ha detectado un objeto de interés.{RESET_COLOR}")
        send_alert(detected_items, session)

    detection_state.last_detection_time = time.time()

def draw_labels_on_frame(frame, detected_items):
    for idx, (label, confidence) in enumerate(detected_items):
        cv2.putText(frame, f"{label}: {confidence:.2f}%", 
                    (10, 30 * (idx + 1)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    return frame
 
def draw_labels_on_frame(frame, detected_items):
    for idx, (label, confidence) in enumerate(detected_items):
        cv2.putText(frame, f"{label}: {confidence:.2f}%", 
                    (10, 30 * (idx + 1)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    return frame

def save_video_segment(frames, start_time, session, detected_items):
    video_filename = f"{start_time:.2f}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = os.path.join(settings.BASE_DIR, video_filename)

    height, width, _ = frames[0][0].shape
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 10, (width, height))

    for frame, _ in frames:
        out.write(frame)

    out.release()
    print(f"{GREEN_COLOR}Segmento de video guardado: {video_filename}{RESET_COLOR}")

    # Preparar la información de las armas detectadas
    weapons_info = f'{', '.join(item[0] for item in detected_items)}'

    # Enviar el video por correo
    try:
        is_weapon = True
        recipient_email = session.user.email
        context = {
            'session': session,
            'weapons_detected': weapons_info,
            'weapons_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'is_weapon': is_weapon
        }

        send_alert_email_video(
            subject=f'Detección de arma en la sesión {session.id}',
            template_name='email_content.html',
            context=context,
            recipient_list=[recipient_email],
            attachment_path=video_path,
            attachment_name=video_filename
        )
        print(f"{GREEN_COLOR}Correo enviado correctamente.{RESET_COLOR}")

        os.remove(video_path)
        print(f"{GREEN_COLOR}Archivo {video_filename} eliminado después de enviar el correo.{RESET_COLOR}")
    except Exception as e:
        print(f"{RED_COLOR}Error al enviar el correo o leer el archivo: {e}{RESET_COLOR}")
        
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
                
    alert_message = f"{YELLOW_COLOR}¡Alerta! Se ha detectado un objeto de interés: {', '.join(item[0] for item in detected_items)}{RESET_COLOR}"
    print(alert_message)

    return alert_message
