import cv2
import numpy as np
from app.alarm.models import Alarm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import time

# Cargar el modelo preentrenado MobileNet SSD solo una vez
net = cv2.dnn.readNetFromCaffe('deploy.prototxt', 'mobilenet_ssd.caffemodel')

# Clases de objetos que puede detectar el modelo
classes = ["background", "cell phone", "laptop", "glasses", "handbag"]  # Clases específicas que queremos detectar

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def detect_dropped_item(frame, session):
    global last_email_time

    height, width = frame.shape[:2]
    
    # Preparar la imagen para el modelo MobileNet SSD
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5, False)
    net.setInput(blob)
    detections = net.forward()

    people = []
    objects = []
    dropped_items = []

    # Procesamos las detecciones
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:  # Umbral de confianza
            class_id = int(detections[0, 0, i, 1])
            obj_class = classes[class_id]

            # Obtener las coordenadas de la caja delimitadora
            box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
            (x, y, x2, y2) = box.astype("int")
            
            # Clasificamos las detecciones como personas u objetos específicos
            if obj_class == "person":
                people.append((x, y, x2, y2))
            elif obj_class in ["cell phone", "laptop", "glasses", "handbag"]:  # Solo los objetos deseados
                objects.append((x, y, x2, y2, obj_class))

    # Detectamos si hay objetos caídos
    for (x, y, x2, y2, obj_class) in objects:
        if y > height // 2:  # Consideramos caído si está en la mitad inferior de la imagen
            is_near_person = False
            for (px, py, px2, py2) in people:
                if abs(px - x) < 50 and abs(py - y) < 50:  # Si está muy cerca de una persona, no lo consideramos caído
                    is_near_person = True
                    break

            if not is_near_person:
                dropped_items.append((x, y, x2, y2, obj_class))

    # Activar alarma y enviar correo si se detecta un objeto caído
    if dropped_items:
        for (x, y, x2, y2, obj_class) in dropped_items:
            cv2.rectangle(frame, (x, y), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f'Objeto caído: {obj_class}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        alarm = Alarm.objects.filter(detection=session.detection_models.first(), user=session.user, is_active=True).first() 
        if alarm:
            alarm.activate()
        else:
            default_alarm = Alarm()
            default_alarm.play_default_alarm()

        current_time = time.time()

        # Verificar si ha pasado suficiente tiempo desde el último correo
        if current_time - last_email_time > EMAIL_COOLDOWN:
            _, buffer = cv2.imencode('.jpg', frame)
            image_content = buffer.tobytes()

            # Enviar correo con la imagen, el contexto y el objeto detectado
            send_dropped_item_alert_email(session, image_content, dropped_items)
            last_email_time = current_time
    else:
        Alarm.stop_alarm()

    return frame

def send_dropped_item_alert_email(session, image_content, dropped_items):
    # Crear el contexto del correo
    context = {
        'session': session,
        'dropped_items': dropped_items,
    }

    html_content = render_to_string('emails/dropped_item_alert.html', context)
    text_content = strip_tags(html_content)

    subject = f'Alerta de objeto caído en la sesión {session.id}'
    from_email = settings.EMAIL_HOST_USER
    to = ['duranalexis879@gmail.com']
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.attach('objeto_caido_detectado.jpg', image_content, 'image/jpeg')

    # Enviar el correo
    msg.send(fail_silently=False)
