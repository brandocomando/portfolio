"""Temporal Worker for Portfolio MLOps Pipeline."""

import asyncio
import os
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from mlops.workflows.knowledge_sync_workflow import KnowledgeSyncWorkflow
from mlops.workflows.activities import (
    ingest_bronze_activity,
    transform_silver_activity,
    build_gold_activity,
    evaluate_benchmark_activity,
    publish_artifacts_activity
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portfolio.temporal.worker")

TASK_QUEUE = "portfolio-mlops-queue"


async def main():
    temporal_address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    logger.info(f"Connecting Temporal worker to: {temporal_address}")

    client = await Client.connect(temporal_address)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[KnowledgeSyncWorkflow],
        activities=[
            ingest_bronze_activity,
            transform_silver_activity,
            build_gold_activity,
            evaluate_benchmark_activity,
            publish_artifacts_activity
        ]
    )

    logger.info(f"Temporal Worker listening on queue: {TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
