import cv2
from app.alarm.models import Alarm
from datetime import datetime
from app.monitoring.utils.send_email import send_alert_email

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
        alarm = Alarm.objects.filter(detection=session.detection_models.first(), user=session.user, is_active=True).first() 
        if alarm:
            alarm.activate()
        else:
            default_alarm = Alarm()
            default_alarm.play_default_alarm()
        
        current_time = datetime.now()
        
        # Verificar si ha pasado suficiente tiempo desde el último correo
        if current_time.timestamp() - last_email_time > EMAIL_COOLDOWN:
            # Convertir el frame actual a imagen JPEG
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
            last_email_time = current_time.timestamp()
    else:
        Alarm.stop_alarm()

    # Dibujar el estado en la parte superior
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
    cv2.putText(frame, texto_estado, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    return frame
    