from django.http import JsonResponse
from django.views.decorators.http import require_GET
from app.monitoring.models import MonitoringSession
from app.alarm.models import Alarm
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

@require_GET
def get_notifications(request, session_id):
    try:
        session = MonitoringSession.objects.get(id=session_id)
        detection_id = session.detection_model.id
        recent_time_threshold = timezone.now() - timedelta(seconds=10)
        
        cache_key = f'camera_error_{session_id}'
        last_error_time = cache.get(cache_key)
        current_time = timezone.now()
        
        if not session.camera_status:
            if last_error_time is None or (current_time - last_error_time).seconds >= 5:
                cache.set(cache_key, current_time, 60)
                return JsonResponse({
                    'notifications': [
                        {
                            'message': 'No se pudo abrir la cámara o se detuvo la conexión.<br>Por favor, verifique si la IP de la cámara es correcta.',
                            'tags': 'error',
                            'timestamp': current_time.isoformat()
                        }
                    ]
                })
            return JsonResponse({'notifications': []})
            
        alerts = Alarm.objects.filter(
            detection_id=detection_id,
            is_active=True,
            last_activated__gte=recent_time_threshold
        )
        
        notifications = []
        for alert in alerts:
            notifications.append({
                'message': alert.notification_message,
                'tags': 'warning',
                'timestamp': alert.last_activated.isoformat()
            })
        return JsonResponse({'notifications': notifications})
    except MonitoringSession.DoesNotExist:
        return JsonResponse({'error': 'Sesión no encontrada'}, status=404)
    except Exception as e:
        print(f"Error en get_notifications: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)