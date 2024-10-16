import cv2
from app.alarm.models import Alarm
from datetime import datetime, timedelta
from app.monitoring.utils.send_email import send_alert_email
from app.threat_management.models import DetectionCounter
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Objeto de la clase BackgroundSubtractorMOG2
fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

# Cooldown para detecciones
COOLDOWN_TIME = timedelta(seconds=10)

# Inicializar la última detección
last_detection_time = None

# Crear un ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

def process_contour(cnt):
    if cv2.contourArea(cnt) > 500:
        return cv2.boundingRect(cnt)
    return None

def send_email_async(session, current_time, frame):
    _, buffer = cv2.imencode('.jpg', frame)
    image_content = buffer.tobytes()

    recipient_email = session.user.email
    context = {
        'session': session,
        'activation_time': current_time.strftime("%d/%m/%Y %H:%M:%S")
    }
    send_alert_email(
        subject=f'Alerta de movimiento en la sesión {session.id}',
        template_name='email_content.html',
        context=context,
        image_content=image_content,
        image_name='movimiento_detectado.jpg',
        recipient_list=[recipient_email]
    )

def detect_motion(frame, session, frame_index, fps):
    global last_email_time, last_detection_time
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crear una máscara para detectar el movimiento
    fgmask = fgbg.apply(gray)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    # Encontrar contornos en la máscara
    cnts, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False

    # Procesar contornos en paralelo
    results = list(executor.map(process_contour, cnts))
    rectangles = [rect for rect in results if rect is not None]

    if rectangles:
        motion_detected = True
        for (x, y, w, h) in rectangles:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Calcular el tiempo actual basado en el índice del frame y los FPS
    current_time = datetime.now() + timedelta(seconds=frame_index / fps)

    if motion_detected:
        # Comprobar si ha pasado suficiente tiempo desde la última detección
        if last_detection_time is None or current_time - last_detection_time > COOLDOWN_TIME:
            last_detection_time = current_time  # Actualizar el tiempo de la última detección
            
            detection = session.detection_models.first()
            
            # Obtener o crear el contador de detección
            detection_counter, created = DetectionCounter.objects.get_or_create(
                detection=detection,
                user=session.user
            )
            detection_counter.increment()  # Incrementar el contador de detecciones
            
            # Activar la alarma
            alarm = Alarm.objects.filter(detection=detection, user=session.user, is_active=True).first()
                    
            if alarm:
                alarm.activate()
            else:
                default_alarm = Alarm()
                default_alarm.play_default_alarm()

            # Verificar si ha pasado suficiente tiempo desde el último correo
            if current_time.timestamp() - last_email_time > EMAIL_COOLDOWN:
                executor.submit(send_email_async, session, current_time, frame)
                last_email_time = current_time.timestamp()  # Actualizar el tiempo del último correo
    else:
        Alarm.stop_alarm()

    return frame