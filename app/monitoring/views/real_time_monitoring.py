import importlib
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from app.monitoring.models import MonitoringSession
import cv2
from django.http import StreamingHttpResponse
from django.contrib import messages
from app.monitoring.models import MonitoringSession
from django.utils.translation import gettext_lazy as _  # Para traducir las variables dinámicas
import numpy as np
import asyncio
import threading

class RealTimeMonitoringView(View):
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        if session.user != request.user:
            messages.error(request, 'No tienes permiso para acceder a esta sesión de monitoreo.')
            return render(request, 'monitoring_session.html', status=403)

        detection = session.detection_models.all()

        context = {
            'session_id': session_id,
            'session': session,
            'detections': detection,
            'title1': _('Real-Time Monitoring'),
            'title2': _('Monitoring Session: ') + f'{session.id}',
            'details': f'{session.name} - {session.description}'
        }
        
        return render(request, 'real_time_monitoring.html', context)

class VideoStreamView(View):
    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session), content_type="multipart/x-mixed-replace; boundary=frame")

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
            print(f"Intentando importar el módulo: {selected_module['module']}")
            detection_module = importlib.import_module(selected_module['module'])
            print(f"Módulo importado correctamente: {detection_module}")
            detection_function = getattr(detection_module, selected_module['function'])
            print(f"Función de detección encontrada: {detection_function}")
            return detection_function
        except ImportError as e:
            print(f"Error en la importación del módulo '{selected_module['module']}': {str(e)}")
        except AttributeError as e:
            print(f"Error al obtener la función de detección: {str(e)}")
        
        return None

    def gen_frames(self, detection_function, session):
        import queue
        camera = cv2.VideoCapture(0)
        frame_queue = queue.Queue(maxsize=10)
        stop_event = threading.Event()

        def capture_frames():
            frame_index = 0
            fps = camera.get(cv2.CAP_PROP_FPS) or 30
            detection_interval = 5  # Analizar cada 5 frames para detect_objects_in_frame

            while not stop_event.is_set():
                success, frame = camera.read()
                if not success:
                    break

                if detection_function:
                    if detection_function.__name__ == 'detect_objects_in_frame':
                        # Usar la lógica específica para detect_wr (cada x frames)
                        if frame_index % detection_interval == 0:
                            frame = detection_function(frame, session, frame_index, fps)
                    else:
                        # Para otras funciones de detección, procesar cada frame
                        frame = detection_function(frame, session, frame_index, fps)

                try:
                    frame_queue.put(frame, block=False)
                except queue.Full:
                    try:
                        frame_queue.get_nowait()  # Descartar el frame más antiguo
                        frame_queue.put(frame, block=False)
                    except queue.Empty:
                        pass

                frame_index += 1

            camera.release()

        thread = threading.Thread(target=capture_frames)
        thread.start()

        try:
            while True:
                frame = frame_queue.get()
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            stop_event.set()
            thread.join()
              
    def stream_without_detection(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        return StreamingHttpResponse(self.gen_frames(None, session), content_type="multipart/x-mixed-replace; boundary=frame")