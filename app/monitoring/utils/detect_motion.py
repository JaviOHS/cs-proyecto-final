import cv2
import numpy as np
from app.alarm.models import Alarm

# Objeto de la clase BackgroundSubtractorMOG2
fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

def detect_motion(frame, session):
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

    # Activar o detener la alarma según se detecte o no movimiento
    if motion_detected:
        alarm = Alarm.objects.get(detection=session.detection_models.first(), is_active=True)
        alarm.activate()  # Cambiar aquí para usar el método activate de la instancia Alarm
    else:
        Alarm.stop_alarm()  # Mantener esto para detener la alarma cuando no haya movimiento


    # Dibujar el estado en la parte superior
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    return frame
