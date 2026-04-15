import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def publish_agent_registered_event(self, payload: dict) -> None:
    logger.info("AgentRegistered event published: %s", payload)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def publish_agent_status_changed_event(self, payload: dict) -> None:
    logger.info("AgentStatusChanged event published: %s", payload)
