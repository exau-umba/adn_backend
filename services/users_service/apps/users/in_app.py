from .models import InAppNotification


def create_in_app_notification(*, user, title: str, body: str, category: str = "info"):
    return InAppNotification.objects.create(user=user, title=title, body=body, category=category)
