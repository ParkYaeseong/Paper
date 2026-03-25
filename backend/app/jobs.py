from __future__ import annotations

from rq import Worker

from app.config import get_settings
from app.queue import get_queue, get_redis_connection
from app.services.pipeline_runner import process_pipeline_job


def main() -> None:
    settings = get_settings()
    connection = get_redis_connection(settings)
    queue = get_queue(settings)
    worker = Worker([queue], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
