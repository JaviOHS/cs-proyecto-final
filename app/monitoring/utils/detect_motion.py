import cv2
import numpy as np
from app.alarm.models import Alarm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import time

# Objeto de la clase BackgroundSubtractorMOG2
fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def detect_motion(frame, session):
    global last_email_time
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Crear una máscara para detectar el movimiento
    fgmask = fgbg.apply(gray)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    fgmask = cv2.dilate(fgmask, None, iterations=2)

    # Encontrar contornos en la máscara
    cnts, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    texto_estado = "Estado: Sin novedades..."
    color = (225, 0, 0)
    motion_detected = False

    # Dibujar rectángulos alrededor de las áreas de movimiento detectado
    for cnt in cnts:
        if cv2.contourArea(cnt) > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            texto_estado = "Estado: ALERTA Movimiento Detectado!"
            color = (0, 0, 255)
            motion_detected = True

    # Activar la alarma si se detecta movimiento
    if motion_detected:
        alarm = Alarm.objects.get(detection=session.detection_models.first(), is_active=True)
        alarm.activate()

        # Verificar si ha pasado suficiente tiempo desde el último correo
        current_time = time.time()
        if current_time - last_email_time > EMAIL_COOLDOWN:
            # Convertir el frame actual a imagen JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            image_content = buffer.tobytes()

            # Enviar correo con la imagen y el contexto
            send_motion_alert_email(session, image_content)
            last_email_time = current_time
    else:
        Alarm.stop_alarm()

    # Dibujar el estado en la parte superior
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    return frame

def send_motion_alert_email(session, image_content):
    # Crear el contexto del correo
    context = {
        'session': session,
    }
    
    # Renderizar el contenido HTML del correo usando la plantilla
    html_content = render_to_string('emails/motion_alert.html', context)
    
    # Crear una versión de texto plano del contenido HTML
    text_content = strip_tags(html_content)

    # Crear el mensaje de correo
    subject = f'Alerta de movimiento en la sesión {session.id}'
    from_email = settings.EMAIL_HOST_USER
    to = ['duranalexis879@gmail.com']  # Cambia esto por el correo de destino
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")

    # Adjuntar la imagen capturada
    msg.attach('movimiento_detectado.jpg', image_content, 'image/jpeg')

    # Enviar el correo
    msg.send(fail_silently=False)