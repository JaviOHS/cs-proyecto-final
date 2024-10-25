import cv2
from app.alarm.models import Alarm
from datetime import datetime, timedelta
from app.monitoring.utils.send_email import send_alert_email_video
from app.threat_management.models import DetectionCounter
from concurrent.futures import ThreadPoolExecutor
import os
from config.utils import RED_COLOR, GREEN_COLOR, RESET_COLOR, YELLOW_COLOR

fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

EMAIL_COOLDOWN = 10  
last_email_time = 0

COOLDOWN_TIME = timedelta(seconds=3) 

executor = ThreadPoolExecutor(max_workers=4)

is_movement_event_active = False
frames_buffer = []
frames_without_motion = 0 
MIN_FRAMES_WITHOUT_MOTION = 30  
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
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    fgmask = fgbg.apply(gray)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    cnts, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    rectangles = [process_contour(cnt) for cnt in cnts if process_contour(cnt) is not None]

    if rectangles:
        motion_detected = True
        frames_without_motion = 0  
        for (x, y, w, h) in rectangles:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        if not is_movement_event_active:
            is_movement_event_active = True
            alarm_triggered = False 
            frames_buffer = [] 
            print(f"{RED_COLOR}Evento de movimiento iniciado.{RESET_COLOR}")
        
        frames_buffer.append(frame)

        if not alarm_triggered:
            alarm_triggered = True
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

    else:
        if is_movement_event_active:
            frames_without_motion += 1
            print(f"{YELLOW_COLOR}Frame {frame_index} - Frames sin movimiento: {frames_without_motion}/{MIN_FRAMES_WITHOUT_MOTION}{RESET_COLOR}")

            if frames_without_motion >= MIN_FRAMES_WITHOUT_MOTION:
                print(f"{YELLOW_COLOR}Evento de movimiento finalizado.{RESET_COLOR}")
                is_movement_event_active = False
                frames_without_motion = 0
                Alarm.stop_alarm()  

             
                event_id = datetime.now().timestamp()
                video_path = save_video_segment(frames_buffer, event_id)
                executor.submit(send_email_with_video, session, video_path, event_id)

    return frame
