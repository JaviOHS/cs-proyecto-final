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
        detection_ids = session.detection_models.values_list('id', flat=True)
        recent_time_threshold = timezone.now() - timedelta(seconds=20)

        alerts = Alarm.objects.filter(
            detection_id__in=detection_ids,
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
        return JsonResponse({'error': str(e)}, status=500)
