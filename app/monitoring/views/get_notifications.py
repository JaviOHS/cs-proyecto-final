from django.http import JsonResponse
from django.views.decorators.http import require_GET
from app.monitoring.models import MonitoringSession
from app.alarm.models import Alarm
from django.utils import timezone
from datetime import timedelta

@require_GET
def get_notifications(request, session_id):
    try:
        session = MonitoringSession.objects.get(id=session_id)
        
        detection_id = session.detection_model.id  # Obtiene el ID del modelo de detección
        recent_time_threshold = timezone.now() - timedelta(seconds=10)

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
