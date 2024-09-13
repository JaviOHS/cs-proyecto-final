import importlib
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from app.monitoring.models import MonitoringSession
import cv2
from django.http import StreamingHttpResponse
from django.contrib import messages

class RealTimeMonitoringView(View):
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        if session.user != request.user:
            messages.error(request, 'No tienes permiso para acceder a esta sesión de monitoreo.')
            return render(request, 'monitoring_session.html', status=403)

        detection = session.detection_models.first() # Obtener el primer modelo de detección de la sesión (Temporal)

        context = {
            'session': session,
            'title1': 'Monitoreo en Tiempo Real',
            'title2': f'Sesión de Monitoreo: {session.id}',
            'details': f'{session.name} - {detection} - {session.description}'
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
        except ValueError as e:
            messages.warning(request, f"Advertencia: {str(e)}. Se mostrará el video sin procesamiento.")
            return self.stream_without_detection(request, session_id)
        except ImportError as e:
            messages.warning(request, f"Error al cargar el módulo de detección: {str(e)}. Se mostrará el video sin procesamiento.")
            return self.stream_without_detection(request, session_id)

        return StreamingHttpResponse(self.gen_frames(detection_function, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session), content_type="multipart/x-mixed-replace; boundary=frame")

    def load_detection_module(self, detection_id):
        detection_modules = {
            1: {'module': 'app.monitoring.utils.test', 'function': 'test_function'},
            2: {'module': 'app.monitoring.utils.test', 'function': 'test_function'},
            3: {'module': 'app.monitoring.utils.test', 'function': 'test_function'},
            4: {'module': 'app.monitoring.utils.detect_motion', 'function': 'detect_motion'},
        }

        selected_module = detection_modules.get(detection_id)
        if selected_module is None:
            raise ValueError(f"No se encontró un módulo de detección para el ID '{detection_id}'")

        detection_module = importlib.import_module(selected_module['module'])
        detection_function = getattr(detection_module, selected_module['function'], None)
        if not callable(detection_function):
            raise ValueError(f"La función '{selected_module['function']}' no está presente en el módulo '{selected_module['module']}'")

        return detection_function

    def gen_frames(self, detection_function, session):
        camera = cv2.VideoCapture(0)
        while True:
            success, frame = camera.read()
            if not success:
                break
            if detection_function:
                frame = detection_function(frame, session)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        camera.release()