import json
from django.conf import settings
import pika


def publish_notification_event(payload: dict):
    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
        channel.queue_declare(queue=settings.NOTIFICATION_EMAIL_QUEUE, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=settings.NOTIFICATION_EMAIL_QUEUE,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
    finally:
        connection.close()


def publish_email_event(payload: dict):
    enriched_payload = {
        "channel": "email",
        **payload,
    }
    publish_notification_event(enriched_payload)

