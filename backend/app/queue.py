from __future__ import annotations

from redis import Redis
from rq import Queue

from app.config import Settings


QUEUE_NAME = "paper"


def get_redis_connection(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url)


def get_queue(settings: Settings) -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection(settings))


def enqueue_pipeline_job(settings: Settings, job_id: str) -> str:
    queue = get_queue(settings)
    job = queue.enqueue("app.jobs.process_pipeline_job", job_id, job_id=job_id)
    return str(job.id)
