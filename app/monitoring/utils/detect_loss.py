import cv2
import numpy as np
from app.alarm.models import Alarm
import time
from app.monitoring.utils.send_email import send_alert_email

net = cv2.dnn.readNetFromCaffe('deploy.prototxt', 'mobilenet_ssd.caffemodel')

classes = ["background", "cell phone", "laptop", "glasses", "handbag"]

last_email_time = 0
EMAIL_COOLDOWN = 10

def detect_dropped_item(frame, session):
    global last_email_time

    height, width = frame.shape[:2]
    
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5, False)
    net.setInput(blob)
    detections = net.forward()

    people = []
    objects = []
    dropped_items = []

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            class_id = int(detections[0, 0, i, 1])
            obj_class = classes[class_id]

            box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
            (x, y, x2, y2) = box.astype("int")
            
            if obj_class == "person":
                people.append((x, y, x2, y2))
            elif obj_class in ["cell phone", "laptop", "glasses", "handbag"]:
                objects.append((x, y, x2, y2, obj_class))

    for (x, y, x2, y2, obj_class) in objects:
        if y > height // 2:
            is_near_person = False
            for (px, py, px2, py2) in people:
                if abs(px - x) < 50 and abs(py - y) < 50:
                    is_near_person = True
                    break

            if not is_near_person:
                dropped_items.append((x, y, x2, y2, obj_class))

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

        if current_time - last_email_time > EMAIL_COOLDOWN:
            _, buffer = cv2.imencode('.jpg', frame)
            image_content = buffer.tobytes()

            recipient_email = session.user.email
            is_dropped_item = True
            context = {
                'session': session,
                'activation_time': time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(current_time)),
                'dropped_items': dropped_items,
                'is_dropped_item': is_dropped_item
            }
            send_alert_email(
                subject=f'Alerta de objeto caído en la sesión {session.id}',
                template_name='email_content.html',
                context=context,
                image_content=image_content,
                image_name='objeto_caido_detectado.jpg',
                recipient_list=[recipient_email]
            )
            last_email_time = current_time
    else:
        Alarm.stop_alarm()

    return frame