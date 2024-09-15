import boto3
import cv2
from botocore.exceptions import ClientError
from django.conf import settings
from app.alarm.models import Alarm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import time

rekognition = boto3.client('rekognition',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

# Variable para rastrear el tiempo del último correo enviado
last_email_time = 0
EMAIL_COOLDOWN = 10  # Enviar correos cada 10 segundos

def detect_crowding(frame, session):
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
        alarm = Alarm.objects.get(detection=session.detection_models.first(), is_active=True)
        if crowding_detected:
            alarm.activate()
            
            # Verificar si ha pasado suficiente tiempo desde el último correo
            current_time = time.time()
            if current_time - last_email_time > EMAIL_COOLDOWN:
                # Enviar correo con la imagen y el contexto
                send_crowding_alert_email(session, frame_bytes, num_people)
                last_email_time = current_time
        else:
            Alarm.stop_alarm()
    except Alarm.DoesNotExist:
        print("No se encontró una alarma activa para esta sesión.")
    except Exception as e:
        print(f"Error al manejar la alarma: {e}")

    return frame

def send_crowding_alert_email(session, image_content, num_people):
    # Crear el contexto del correo
    context = {
        'session': session,
        'num_people': num_people,
        'threshold': session.crowding_threshold
    }
    
    # Renderizar el contenido HTML del correo usando la plantilla
    html_content = render_to_string('emails/motion_crowding.html', context)
    
    # Crear una versión de texto plano del contenido HTML
    text_content = strip_tags(html_content)

    # Crear el mensaje de correo
    subject = f'Alerta de aglomeración en la sesión {session.id}'
    from_email = settings.EMAIL_HOST_USER
    to = ['duranalexis879@gmail.com']  # Cambia esto por el correo de destino
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")

    # Adjuntar la imagen capturada
    msg.attach('aglomeracion_detectada.jpg', image_content, 'image/jpeg')

    # Enviar el correo
    msg.send(fail_silently=False)