from celery import shared_task
from django.utils import timezone
from .models import ChildRoutine
from apps.users.models import ParentDevice
from .notifications import send_push_notification
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_and_send_routine_notifications():
    """
    Scheduled task that runs every minute to check for routines
    that need to notify parents.
    """
    now = timezone.now()
    # Ensure we use the correct timezone for the user/system
    current_time = now.strftime("%H:%M")
    current_day = now.weekday() # 0 = Monday, 6 = Sunday

    # Find active routines scheduled for this time and day
    # We use __contains for repeat_days check (comma-separated string)
    routines = ChildRoutine.objects.filter(
        is_active=True,
        notify_parent=True,
        time__hour=now.hour,
        time__minute=now.minute
    )

    for routine in routines:
        # Double check the day
        if str(current_day) in routine.repeat_days.split(','):
            # 1. Notify the child's own devices
            child_devices = routine.child.devices.all()
            for device in child_devices:
                logger.info(f"Sending notification to child {routine.child.email}")
                send_push_notification(
                    token=device.fcm_token,
                    title="NeuroLearn Routine",
                    body=f"It's time for: {routine.title}",
                    data={"routine_id": str(routine.id)}
                )

            # 2. Notify parent(s) for this child
            parents = routine.child.child_profile.parents.all()
            for parent in parents:
                # Find devices for this parent
                devices = parent.user.devices.all()
                for device in devices:
                    title = "NeuroLearn Reminder"
                    body = f"Time for {routine.title} for {routine.child.first_name}"
                    
                    logger.info(f"Sending notification to parent {parent.user.email}")
                    send_push_notification(
                        token=device.fcm_token,
                        title=title,
                        body=body,
                        data={"routine_id": str(routine.id), "child_id": str(routine.child.id)}
                    )
