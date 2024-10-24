import importlib
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
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

video_lock = threading.Lock()
class VideoStreamView(View):
    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        detection = session.detection_model
        if not detection:
            messages.warning(request, 'No hay un modelo de detección válido asociado con esta sesión. Se mostrará el video sin procesamiento.')
            return self.stream_without_detection(request, session_id)

        try:
            detection_function = self.load_detection_module(detection.id)
            if detection_function is None:
                raise ValueError(f"No se pudo cargar la función de detección para el ID {detection.id}")
        except Exception as e:
            messages.warning(request, f"Error al cargar el módulo de detección: {str(e)}. Se mostrará el video sin procesamiento.")
            return self.stream_without_detection(request, session_id)
        return StreamingHttpResponse(self.gen_frames(detection_function, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def load_detection_module(self, detection_id):
        detection_modules = {
            1: {'module': 'app.monitoring.utils.detect_theft', 'function': 'detect_theft'},
            2: {'module': 'app.monitoring.utils.detect_drop_items', 'function': 'detect_drop_items'},
            3: {'module': 'app.monitoring.utils.detect_crowding', 'function': 'detect_crowding'},
            4: {'module': 'app.monitoring.utils.detect_motion', 'function': 'detect_motion'},
            5: {'module': 'app.monitoring.utils.detect_aggression', 'function': 'detect_aggression'},
            6: {'module': 'app.monitoring.utils.detect_wr', 'function': 'detect_objects_in_frame'}
        }

        selected_module = detection_modules.get(detection_id)
        if selected_module is None:
            raise ValueError(f"No se encontró un módulo de detección para el ID '{detection_id}'")
        try:
            print(f"Cargando módulo de detección: {selected_module['module']}")
            detection_module = importlib.import_module(selected_module['module'])
            detection_function = getattr(detection_module, selected_module['function'])
            print(f"Función de detección cargada: {detection_function.__name__}")
            return detection_function
        except ImportError as e:
            print(f"Error en la importación del módulo '{selected_module['module']}': {str(e)}")
        except AttributeError as e:
            print(f"Error al obtener la función de detección: {str(e)}")
        return None

    def gen_frames(self, detection_function, session):
        import queue
        camera_ip = session.camera_ip 
        camera_url = 0 if camera_ip is None else f'http://{camera_ip}/video'
        camera = cv2.VideoCapture(camera_url)
        if not camera.isOpened():
            print(f"No se pudo abrir la cámara en la URL: {camera_url}")
        camera = cv2.VideoCapture(camera_url)
        frame_queue = queue.Queue(maxsize=10)
        stop_event = threading.Event()
        is_saving_video = threading.Event()
        fps = camera.get(cv2.CAP_PROP_FPS) or 30
        
        def capture_frames():
            frame_index = 0
            while not stop_event.is_set():
                success, frame = camera.read()
                if not success:
                    break
                if frame_queue.full():
                    frame_queue.get()
                frame_queue.put((frame, frame_index))
                frame_index += 1
            camera.release()

        def process_detection():
            while not stop_event.is_set():
                if not frame_queue.empty():
                    frame, frame_index = frame_queue.get()
                    if detection_function and detection_function.__name__ == 'detect_objects_in_frame':
                        from app.monitoring.utils.detect_wr import detection_interval
                        if frame_index % detection_interval == 0:
                            threading.Thread(
                                target=run_detection,
                                args=(frame, session, frame_index, fps, is_saving_video)
                            ).start()
                    elif detection_function.__name__ == 'detect_aggression':
                        from app.monitoring.utils.detect_aggression import detection_interval
                        if frame_index % detection_interval == 0:
                            threading.Thread(
                                target=run_detection,
                                args=(frame, session, frame_index, fps, is_saving_video)
                            ).start()
                    else:
                        threading.Thread(
                            target=run_detection,
                            args=(frame, session, frame_index, fps, is_saving_video)
                        ).start()

        def run_detection(frame, session, frame_index, fps, is_saving_video):
            if not is_saving_video.is_set():
                is_saving_video.set()
                try:
                    frame = detection_function(frame, session, frame_index, fps)
                finally:
                    is_saving_video.clear()
                    
        threading.Thread(target=capture_frames, daemon=True).start()
        threading.Thread(target=process_detection, daemon=True).start()
        
        try:
            while True:
                if not frame_queue.empty():
                    frame, _ = frame_queue.get()
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            stop_event.set()
