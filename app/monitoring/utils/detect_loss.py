import cv2
import numpy as np
from app.alarm.models import Alarm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import time

# Cargamos el modelo YOLO preentrenado
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Clases de objetos que puede detectar el modelo
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def detect_dropped_item(frame, session):
    global last_email_time

    height, width, _ = frame.shape

    # Preparar la imagen para YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Inicializamos variables para guardar las detecciones
    people = []
    objects = []
    dropped_items = []

    # Procesamos las detecciones
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > 0.5:  # Umbral de confianza
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Obtener las coordenadas de la caja
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # Clasificamos las detecciones como personas o objetos
                if classes[class_id] == "person":
                    people.append((x, y, w, h))  # Guardar las coordenadas de las personas
                elif classes[class_id] in ["handbag", "suitcase", "backpack", "cell phone", "book", "laptop"]:  # Objetos que podrían caerse
                    objects.append((x, y, w, h, classes[class_id]))  # Guardar las coordenadas y el tipo de objeto

    # Revisamos si hay objetos que se han "caído"
    for (x, y, w, h, obj_class) in objects:
        # Si el objeto está en el suelo y no está cerca de ninguna persona, consideramos que se ha caído
        if y > height // 2:  # Consideramos objetos en la mitad inferior de la imagen como caídos
            is_near_person = False
            for (px, py, pw, ph) in people:
                if abs(px - x) < 50 and abs(py - y) < 50:  # Si está muy cerca de una persona, no lo consideramos caído
                    is_near_person = True
                    break
            
            if not is_near_person:
                dropped_items.append((x, y, w, h, obj_class))

    # Activar alarma y enviar correo si se detecta un objeto caído
    if dropped_items:
        for (x, y, w, h, obj_class) in dropped_items:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
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
            # Convertir el frame actual a imagen JPEG
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
    
    # Renderizar el contenido HTML del correo usando la plantilla
    html_content = render_to_string('emails/dropped_item_alert.html', context)
    
    # Crear una versión de texto plano del contenido HTML
    text_content = strip_tags(html_content)

    # Crear el mensaje de correo
    subject = f'Alerta de objeto caído en la sesión {session.id}'
    from_email = settings.EMAIL_HOST_USER
    to = ['duranalexis879@gmail.com']  # Cambia esto por el correo de destino
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")

    # Adjuntar la imagen capturada
    msg.attach('objeto_caido_detectado.jpg', image_content, 'image/jpeg')

    # Enviar el correo
    msg.send(fail_silently=False)
