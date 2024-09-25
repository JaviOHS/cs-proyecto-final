import importlib
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from app.monitoring.models import MonitoringSession
import cv2
from django.http import StreamingHttpResponse
from django.contrib import messages
from app.monitoring.models import MonitoringSession
from app.monitoring.utils.detect_crowding import detect_crowding
from app.monitoring.utils.detect_motion import detect_motion

class RealTimeMonitoringView(View):
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        if session.user != request.user:
            messages.error(request, 'No tienes permiso para acceder a esta sesión de monitoreo.')
            return render(request, 'monitoring_session.html', status=403)

        detection = session.detection_models.all()

        context = {
            'session': session,
            'detections': detection,
            'title1': 'Monitoreo en Tiempo Real',
            'title2': f'Sesión de Monitoreo: {session.id}',
            'details': f'{session.name} - {session.description}'
        }
        
        return render(request, 'real_time_monitoring.html', context)

class VideoStreamView(View):
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        if session.user != request.user:
            messages.error(request, 'No tienes permiso para acceder a esta sesión de monitoreo.')
            return redirect(reverse('monitoring:monitoring_session'))

        detection = session.detection_models.first()
        if not detection:
            messages.warning(request, 'No hay un modelo de detección válido asociado con esta sesión. Se mostrará el video sin procesamiento.')
            return self.stream_without_detection(request, session_id)

        try:
            detection_function = self.load_detection_module(detection.id)
        except Exception as e:
            messages.warning(request, f"Error al cargar el módulo de detección: {str(e)}. Se mostrará el video sin procesamiento.")
            return self.stream_without_detection(request, session_id)

        return StreamingHttpResponse(self.gen_frames(detection_function, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def load_detection_module(self, detection_id):
        detection_modules = {
            1: {'module': 'app.monitoring.utils.detect_theft', 'function': 'detect_theft'},
            2: {'module': 'app.monitoring.utils.detect_loss', 'function': 'detect_loss'},
            3: {'module': 'app.monitoring.utils.detect_crowding', 'function': 'detect_crowding'},
            4: {'module': 'app.monitoring.utils.detect_motion', 'function': 'detect_motion'},
        }

        selected_module = detection_modules.get(detection_id)
        if selected_module is None:
            raise ValueError(f"No se encontró un módulo de detección para el ID '{detection_id}'")

        try:
            detection_module = importlib.import_module(selected_module['module'])
            detection_function = getattr(detection_module, selected_module['function'])
            if not callable(detection_function):
                raise AttributeError(f"La función '{selected_module['function']}' no es callable")
        except ImportError:
            raise ImportError(f"No se pudo importar el módulo '{selected_module['module']}'")
        except AttributeError as e:
            raise AttributeError(f"Error al obtener la función de detección: {str(e)}")

        return detection_function

    def gen_frames(self, detection_function, session):
        camera = cv2.VideoCapture(0)
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            if detection_function:
                processed_frame = detection_function(frame, session)
            else:
                processed_frame = frame
            
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        camera.release()
        