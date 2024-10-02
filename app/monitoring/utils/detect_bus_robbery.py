import cv2
import numpy as np
from app.alarm.models import Alarm
import time
from math import sqrt
from app.monitoring.utils.send_email import send_alert_email


# Cargar el modelo preentrenado MobileNet SSD
net = cv2.dnn.readNetFromCaffe('deploy.prototxt', 'mobilenet_ssd.caffemodel')

# Clases de objetos que puede detectar el modelo
classes = ["background", "cell phone", "laptop", "glasses", "handbag", "person"]  # Añadir 'person' para detectar personas

# Cooldown por sesión (tiempo del último correo enviado para cada sesión)
email_cooldowns = {}
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def calculate_distance(box1, box2):
    """Calcula la distancia euclidiana entre dos cajas delimitadoras."""
    (x1, y1, x2, y2) = box1
    (x1_2, y1_2, x2_2, y2_2) = box2
    return sqrt((x1 - x1_2) ** 2 + (y1 - y1_2) ** 2)

def detect_suspicious_behavior(frame, session):
    global email_cooldowns
    
    # Inicializar el cooldown para la sesión si no existe
    if session.id not in email_cooldowns:
        email_cooldowns[session.id] = 0

    height, width = frame.shape[:2]
    
    # Preparar la imagen para el modelo MobileNet SSD
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5, False)
    net.setInput(blob)
    detections = net.forward()

    people = []
    objects = []
    suspicious_activity = False

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

    # Detectar aglomeraciones sospechosas
    if len(people) > 1:
        for (px1, py1, px2, py2) in people:
            for (px1_2, py1_2, px2_2, py2_2) in people:
                distance = calculate_distance((px1, py1, px2, py2), (px1_2, py1_2, px2_2, py2_2))
                if distance < 100:  # Si hay dos personas muy cerca usando la distancia euclidiana
                    suspicious_activity = True
                    cv2.putText(frame, "Aglomeración sospechosa", (px1, py1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Activar alarma si se detecta actividad sospechosa
    if suspicious_activity:
        cv2.putText(frame, 'Robo detectado', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Buscar alarmas activas para la sesión actual
        alarm = Alarm.objects.filter(detection=session.detection_models.first(), user=session.user, is_active=True).first()
        if alarm:
            alarm.activate()
        else:
            default_alarm = Alarm()
            default_alarm.play_default_alarm()

        current_time = time.time()

        # Verificar si ha pasado suficiente tiempo desde el último correo
        if current_time - email_cooldowns[session.id] > EMAIL_COOLDOWN:
            _, buffer = cv2.imencode('.jpg', frame)
            image_content = buffer.tobytes()
            
            recipient_email = session.user.email
            context = {
                'session': session,
            }
            send_alert_email(
                subject='¡Posible robo en el bus!',
                template_name='email_content.html',
                context=context,
                image_content=image_content,
                image_name='robo_detectado.jpg',
                recipient_list=[recipient_email]
            )            
    else:
        Alarm.stop_alarm()

    return frame
