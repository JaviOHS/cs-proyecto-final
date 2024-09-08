from django.shortcuts import render, get_object_or_404
from django.views import View
from app.monitoring.models import MonitoringSession
import cv2
from django.http import StreamingHttpResponse

class RealTimeMonitoringView(View):
    def get(self, request, session_id):
        session = get_object_or_404(MonitoringSession, id=session_id)
        
        # Verificar que el usuario actual es el propietario de la sesión
        if session.user != request.user:
            return render(request, '403.html', status=403)  # O redirige a una página de error de permiso

        context = {
            'session': session,
            'title1': 'Monitoreo en Tiempo Real',
            'title2': f'Sesión de Monitoreo: {session.id}',
            'details': f'{session.name} - {session.description}'
        }
        
        return render(request, 'real_time_monitoring.html', context)

class VideoStreamView(View):
    def get(self, request):
        return StreamingHttpResponse(self.gen_frames(), content_type="multipart/x-mixed-replace; boundary=frame")

    def gen_frames(self):
        # Captura de video desde la cámara
        camera = cv2.VideoCapture(0)

        while True:
            success, frame = camera.read()  # Lee el frame de la cámara
            if not success:
                break
            else:
                # Codificar el frame en formato JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Enviar el frame en el formato adecuado para MJPEG
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        camera.release()
