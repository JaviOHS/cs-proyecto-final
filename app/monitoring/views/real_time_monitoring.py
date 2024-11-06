import importlib
import queue
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
import numpy as np
from app.monitoring.models import MonitoringSession
import cv2
from django.http import StreamingHttpResponse
from django.contrib import messages
from app.monitoring.models import MonitoringSession
from django.utils.translation import gettext_lazy as _
import threading

class RealTimeMonitoringView(View):
    permission_required = 'view_monitoringsession'
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        if session.user != request.user:
            messages.error(request, _('No tienes permiso para acceder a esta sesión de monitoreo.'))
            return redirect('monitoring:monitoring_session')
        detection = session.detection_model
        
        context = {
            'session_id': session_id,
            'session': session,
            'detection': detection,
            'title1': _('Real-Time Monitoring'),
            'title2': _('Monitoring Session: ') + f'{session.id}',
            'details': f'{session.name} - {session.description}'
        }
        return render(request, 'real_time_monitoring.html', context)
    
    
class VideoStreamView(View):
    detection_modules = {
        1: {'module': 'app.monitoring.utils.detect_theft', 'function': 'detect_theft', 'interval': 12},
        2: {'module': 'app.monitoring.utils.detect_drop_items', 'function': 'detect_drop_items', 'interval': 30},
        3: {'module': 'app.monitoring.utils.detect_crowding', 'function': 'detect_crowding', 'interval': 124},
        4: {'module': 'app.monitoring.utils.detect_motion', 'function': 'detect_motion', 'interval': 24},
        5: {'module': 'app.monitoring.utils.detect_aggression', 'function': 'detect_aggression', 'interval': 12},
        6: {'module': 'app.monitoring.utils.detect_wr', 'function': 'detect_objects_in_frame', 'interval': 42}
    }

    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session, 1), content_type="multipart/x-mixed-replace; boundary=frame")

    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        detection = session.detection_model

        if not detection:
            messages.warning(request, 'No hay un modelo de detección válido asociado con esta sesión. Se mostrará el video sin procesamiento.')
            return self.stream_without_detection(request, session_id)

        detection_function, detection_interval = self.load_detection_module(detection.id)
        if detection_function is None:
            messages.warning(request, f"No se pudo cargar la función de detección para el ID {detection.id}. Se mostrará el video sin procesamiento.")
            return self.stream_without_detection(request, session_id)

        return StreamingHttpResponse(self.gen_frames(detection_function, session, detection_interval), content_type="multipart/x-mixed-replace; boundary=frame")

    def load_detection_module(self, detection_id):
        selected_module = self.detection_modules.get(detection_id)
        if not selected_module:
            print(f"No se encontró un módulo de detección para el ID '{detection_id}'")
            return None, None
        try:
            from config.utils import GREEN_COLOR, RESET_COLOR
            detection_module = importlib.import_module(selected_module['module'])
            detection_function = getattr(detection_module, selected_module['function'])
            detection_interval = selected_module['interval']
            print(f"{GREEN_COLOR}Módulo cargado correctamente: '{selected_module['module']}'{RESET_COLOR}")
            return detection_function, detection_interval
        except ImportError as e:
            print(f"Error en la importación del módulo '{selected_module['module']}': {str(e)}")
        except AttributeError as e:
            print(f"Error al obtener la función de detección '{selected_module['function']}': {str(e)}")
        return None, None

    def gen_frames(self, detection_function, session, detection_interval):
        camera_ip = session.camera_ip
        camera_url = 0 if camera_ip is None else f'http://{camera_ip}/video'
        camera = cv2.VideoCapture(camera_url)

        if not camera.isOpened():
            print(f"No se pudo abrir la cámara en la URL: {camera_url}")
            session.camera_status = False
            session.save(update_fields=['camera_status'])
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return

        session.camera_status = True
        session.save(update_fields=['camera_status'])
        frame_queue = queue.Queue(maxsize=10)
        stop_event = threading.Event()
        fps = camera.get(cv2.CAP_PROP_FPS) or 30
        frame_index = 0

        def capture_frames():
            nonlocal frame_index
            while not stop_event.is_set():
                success, frame = camera.read()
                if not success:
                    print("Error al leer el frame. Conexión finalizada o interrumpida.")
                    session.camera_status = False
                    session.save(update_fields=['camera_status'])
                    break

                if detection_function and frame_index % detection_interval == 0:
                    processed_frame = detection_function(frame.copy(), session, frame_index, fps)
                else:
                    processed_frame = frame

                if frame_queue.full():
                    frame_queue.get()
                frame_queue.put(processed_frame)
                frame_index += 1

            camera.release()

        threading.Thread(target=capture_frames, daemon=True).start()

        try:
            while True:
                if not frame_queue.empty():
                    frame = frame_queue.get()
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            stop_event.set()
