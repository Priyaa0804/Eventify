from django.core.mail import send_mail
from .models import Notification


def notify(user, event_request, subject, message):
    if not user or not user.email:
        return
    try:
        send_mail(subject, message, None, [user.email])
        status = 'SENT'
    except Exception:
        status = 'FAILED'
    Notification.objects.create(
        user=user, event_request=event_request, message=message, sent_status=status
    )