import json
import os

import pika
from mailing import dispatch_notification
from test_mail_api import start_mail_test_api_background


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
QUEUE = os.getenv("NOTIFICATION_EMAIL_QUEUE", "notification.email.queue")
MAX_RETRIES = int(os.getenv("NOTIFICATION_MAX_RETRIES", "5"))


def on_message(channel, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        dispatch_notification(payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        headers = properties.headers or {}
        retry_count = int(headers.get("x-retries", 0))
        if retry_count < MAX_RETRIES:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    headers={"x-retries": retry_count + 1},
                ),
            )
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[notification] Send failed: {exc} | retry {retry_count + 1}/{MAX_RETRIES}")
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[notification] Send failed permanently after {MAX_RETRIES} retries: {exc}")


def main():
    start_mail_test_api_background()
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message)
    print(f"[notification] Listening queue: {QUEUE}")
    channel.start_consuming()


if __name__ == "__main__":
    main()
