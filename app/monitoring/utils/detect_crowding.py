import boto3
import cv2
from botocore.exceptions import ClientError
from django.conf import settings
from app.alarm.models import Alarm

rekognition = boto3.client('rekognition',
                           aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           region_name=settings.AWS_REGION)

def detect_crowding(frame, session):
    # Convertir el frame a bytes
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()

    crowding_detected = False

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
        else:
            Alarm.stop_alarm()
    except Alarm.DoesNotExist:
        print("No se encontró una alarma activa para esta sesión.")
    except Exception as e:
        print(f"Error al manejar la alarma: {e}")

    return frame