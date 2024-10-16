import boto3
import cv2
from botocore.exceptions import ClientError
from django.conf import settings
from app.alarm.models import Alarm
import time
from app.monitoring.utils.send_email import send_alert_email
from app.threat_management.models import DetectionCounter

# Inicializar el cliente de Rekognition de AWS
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def detect_crowding(frame, session, frame_index, fps):
    global last_email_time

    # Convertir el frame a bytes
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()

    crowding_detected = False
    num_people = 0

    try:
        # Detectar personas en la imagen usando Rekognition
        response = rekognition.detect_labels(
            Image={'Bytes': frame_bytes},
            MaxLabels=10,
            MinConfidence=80
        )

        # Buscar la etiqueta 'Person'
        person_label = next((label for label in response['Labels'] if label['Name'] == 'Person'), None)

        if person_label:
            # Obtener el número de instancias (personas)
            num_people = len(person_label['Instances'])

            # Dibujar un rectángulo y texto en el frame
            cv2.putText(frame, f'Personas detectadas: {num_people}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Verificar si hay aglomeración
            if num_people > session.crowding_threshold:
                cv2.putText(frame, 'AGLOMERACION DETECTADA', (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                crowding_detected = True

    except ClientError as e:
        print(f"Error al llamar a Rekognition: {e}")

    # Activar o detener la alarma según se detecte o no aglomeración
    try:
        if crowding_detected:
            detection = session.detection_models.first()
            
            # Incrementar el contador de detecciones
            detection_counter, created = DetectionCounter.objects.get_or_create(
                detection=detection,
                user=session.user
            )
            detection_counter.increment()
            
            # Intentar activar una alarma personalizada o reproducir una alarma por defecto
            alarm = Alarm.objects.filter(detection=detection, user=session.user, is_active=True).first()
                    
            if alarm:
                alarm.activate()
            else:
                default_alarm = Alarm()
                default_alarm.play_default_alarm()

            # Enviar un correo si ha pasado suficiente tiempo desde el último correo
            current_time = time.time()
            is_crowding = True
            if current_time - last_email_time > EMAIL_COOLDOWN:
                recipient_email = session.user.email
                context = {
                    'session': session,
                    'num_people': num_people,
                    'threshold': session.crowding_threshold,
                    'frame_index': frame_index,
                    'fps': fps,
                    'is_crowding': is_crowding,
                }
                send_alert_email(
                    subject=f'Alerta de aglomeración en la sesión {session.id}',
                    template_name='email_content.html',
                    context=context,
                    image_content=frame_bytes,
                    image_name='aglomeracion_detectada.jpg',
                    recipient_list=[recipient_email]
                )
                last_email_time = current_time
        else:
            Alarm.stop_alarm()
    except Alarm.DoesNotExist:
        print("No se encontró una alarma activa para esta sesión.")
    except Exception as e:
        print(f"Error al manejar la alarma: {e}")

    return frame
