import boto3
import cv2
from botocore.exceptions import ClientError
from django.conf import settings
from app.alarm.models import Alarm
import time
from app.monitoring.utils.send_email import send_alert_email
from app.threat_management.models import DetectionCounter
from concurrent.futures import ThreadPoolExecutor
from config.utils import RED_COLOR, GREEN_COLOR, RESET_COLOR

rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

last_email_time = 10
EMAIL_COOLDOWN = 10  
executor = ThreadPoolExecutor(max_workers=4)

def call_rekognition(frame_bytes):
    try:
        response = rekognition.detect_labels(
            Image={'Bytes': frame_bytes},
            MaxLabels=10,
            MinConfidence=80
        )
        return response
    except ClientError as e:
        print(f"Error al llamar a Rekognition: {e}")
        return None
    
def detect_crowding(frame, session, frame_index, fps):
    global last_email_time
    crowding_detected = False
    num_people = 0

    _, buffer_original = cv2.imencode('.jpg', frame)
    frame_bytes_original = buffer_original.tobytes()

    future = executor.submit(call_rekognition, frame_bytes_original)
    response = future.result()
    if response:
        person_label = next((label for label in response['Labels'] if label['Name'] == 'Person'), None)
        if person_label:
            num_people = len(person_label['Instances'])
            cv2.putText(frame, f'Personas detectadas: {num_people}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(f"{GREEN_COLOR}Personas detectadas: {num_people}{RESET_COLOR}")
            for instance in person_label['Instances']:
                bounding_box = instance['BoundingBox']
                width, height = frame.shape[1], frame.shape[0]
                
                left = int(bounding_box['Left'] * width)
                top = int(bounding_box['Top'] * height)
                right = int((bounding_box['Left'] + bounding_box['Width']) * width)
                bottom = int((bounding_box['Top'] + bounding_box['Height']) * height)
                
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)  # Verde
                cv2.putText(frame, 'Persona', (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            if num_people > session.crowding_threshold:
                cv2.putText(frame, 'AGLOMERACION DETECTADA', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                print(f"{RED_COLOR}Aglomeración detectada{RESET_COLOR}")
                crowding_detected = True
                
        if crowding_detected:
            _, buffer_processed = cv2.imencode('.jpg', frame)
            frame_bytes_processed = buffer_processed.tobytes()
            
            detection = session.detection_model
            detection_counter, created = DetectionCounter.objects.get_or_create(
                detection=detection,
                user=session.user
            )
            detection_counter.increment()
            
            alarm = Alarm.objects.filter(detection=detection, user=session.user, is_active=True).first()
            if not alarm:
                alarm = Alarm()
                alarm = alarm.create_alarm(detection, session.user)
            if alarm:
                executor.submit(alarm.activate)
            else:
                print("No se pudo crear o encontrar la alarma.")
                
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
                    image_content=frame_bytes_processed,
                    image_name='aglomeracion_detectada.jpg',
                    recipient_list=[recipient_email]
                )
                last_email_time = current_time
                print(f"{GREEN_COLOR}Correo electrónico enviado a {recipient_email}{RESET_COLOR}")

    return frame
