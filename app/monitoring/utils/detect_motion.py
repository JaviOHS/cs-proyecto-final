import cv2
from app.alarm.models import Alarm
from datetime import datetime, timedelta
from app.monitoring.utils.send_email import send_alert_email_video
from app.threat_management.models import DetectionCounter
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import os
from config.utils import RED_COLOR, GREEN_COLOR, RESET_COLOR, YELLOW_COLOR

# Objeto de la clase BackgroundSubtractorMOG2
fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

# Cooldown para correos
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos
last_email_time = 0

# Cooldown para detección de fin de evento de movimiento
COOLDOWN_TIME = timedelta(seconds=3)  # Ajustar según el contexto

# Crear un ThreadPoolExecutor para procesamiento asíncrono
executor = ThreadPoolExecutor(max_workers=4)

# Variables para el manejo de eventos de movimiento
is_movement_event_active = False
frames_buffer = []
frames_without_motion = 0  # Conteo de frames consecutivos sin movimiento
MIN_FRAMES_WITHOUT_MOTION = 30  # Número de frames sin movimiento para considerar el evento finalizado
alarm_triggered = False

def process_contour(cnt):
    if cv2.contourArea(cnt) > 500:
        return cv2.boundingRect(cnt)
    return None

def save_video_segment(frames, event_id):
    video_path = f"movement_event_{event_id}.mp4"
    height, width, layers = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    video = cv2.VideoWriter(video_path, fourcc, 12, (width, height))
    for frame in frames:
        video.write(frame)
    video.release()

    print(f"{GREEN_COLOR}Vídeo del evento de movimiento guardado: {video_path}{RESET_COLOR}")
    return video_path

def send_email_with_video(session, video_path, event_id):
    recipient_email = session.user.email
    current_time = datetime.now()
    context = {
        'session': session,
        'activation_time': current_time.strftime("%d/%m/%Y %H:%M:%S"),
        'event_id': event_id
    }
    
    try:
        send_alert_email_video(
            subject=f"Evento de movimiento detectado en la sesión {session.id}",
            template_name='email_content.html',
            context=context,
            recipient_list=[recipient_email],
            attachment_path=video_path,
            attachment_name=f"movement_event_{event_id}.mp4"
        )
        print(f"{GREEN_COLOR}Correo enviado correctamente con el video del evento {event_id}.{RESET_COLOR}")
    except Exception as e:
        print(f"Error al enviar el correo electrónico: {e}")
    
    os.remove(video_path)
    print(f"{GREEN_COLOR}Vídeo del evento {event_id} eliminado después de enviarlo.{RESET_COLOR}")

def detect_motion(frame, session, frame_index, fps):
    global last_email_time, is_movement_event_active, frames_buffer, frames_without_motion, alarm_triggered
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crear una máscara para detectar el movimiento
    fgmask = fgbg.apply(gray)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    # Encontrar contornos en la máscara
    cnts, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    rectangles = [process_contour(cnt) for cnt in cnts if process_contour(cnt) is not None]

    if rectangles:
        motion_detected = True
        frames_without_motion = 0  # Reiniciar el conteo de frames sin movimiento
        for (x, y, w, h) in rectangles:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Si no hay un evento activo, iniciar uno nuevo
        if not is_movement_event_active:
            is_movement_event_active = True
            alarm_triggered = False  # Resetear el estado de la alarma para el nuevo evento
            frames_buffer = []  # Limpiar el buffer de frames para el nuevo evento
            print(f"{RED_COLOR}Evento de movimiento iniciado.{RESET_COLOR}")
        
        # Agregar el frame al buffer del evento
        frames_buffer.append(frame)

        # Activar la alarma solo la primera vez que se detecta movimiento en un evento
        if not alarm_triggered:
            alarm_triggered = True
            detection = session.detection_models.first()
            detection_counter, created = DetectionCounter.objects.get_or_create(
                detection=detection,
                user=session.user
            )
            detection_counter.increment()
            
            # Activar la alarma de manera asíncrona
            alarm = Alarm.objects.filter(detection=detection, user=session.user, is_active=True).first()
            if alarm:
                executor.submit(alarm.activate)
            else:
                executor.submit(Alarm().play_default_alarm)

    else:
        if is_movement_event_active:
            frames_without_motion += 1
            print(f"{YELLOW_COLOR}Frame {frame_index} - Frames sin movimiento: {frames_without_motion}/{MIN_FRAMES_WITHOUT_MOTION}{RESET_COLOR}")

            # Si se alcanza el umbral de frames sin movimiento, finalizar el evento
            if frames_without_motion >= MIN_FRAMES_WITHOUT_MOTION:
                print(f"{YELLOW_COLOR}Evento de movimiento finalizado.{RESET_COLOR}")
                is_movement_event_active = False
                frames_without_motion = 0
                Alarm.stop_alarm()  # Detener la alarma

                # Guardar y enviar el video del evento
                event_id = datetime.now().timestamp()
                video_path = save_video_segment(frames_buffer, event_id)
                executor.submit(send_email_with_video, session, video_path, event_id)

    return frame
