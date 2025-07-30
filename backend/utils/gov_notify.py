from notifications_python_client.notifications import NotificationsAPIClient

from shared_utils.settings import settings_instance

notifications_client = NotificationsAPIClient(settings_instance.GOV_NOTIFY_API_KEY)


def send_email(user_email: str, meeting_link: str, meeting_title: str):
    notifications_client.send_email_notification(
        email_address=user_email,
        template_id="1ae60bea-3fe2-4f27-ac35-441256ab7a1a",
        personalisation={
            "meeting_link": meeting_link,
            "meeting_title": meeting_title,
        },
    )
