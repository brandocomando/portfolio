import sys
import asyncio
import logging
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mlops.workflows.knowledge_sync_workflow import KnowledgeSyncWorkflow
from mlops.workflows.activities import (
    ingest_bronze_activity,
    transform_silver_activity,
    build_gold_activity,
    evaluate_benchmark_activity,
    publish_artifacts_activity
)

TASK_QUEUE = "portfolio-mlops-queue"


async def run_local_durable_sync():
    print("\n⏳ Initializing Temporal In-Process Server (Zero external dependencies)...")
    async with await WorkflowEnvironment.start_time_skipping() as env:
        worker = Worker(
            env.client,
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

        async with worker:
            print("🚀 Executing KnowledgeSyncWorkflow via Temporal Durable Engine...")
            handle = await env.client.start_workflow(
                KnowledgeSyncWorkflow.run,
                id="knowledge-sync-run-001",
                task_queue=TASK_QUEUE,
            )

            # Query status while running
            status = await handle.query(KnowledgeSyncWorkflow.get_pipeline_status)
            print(f"📊 Initial Pipeline Query: {status['current_step']}")

            # Wait for workflow completion
            result = await handle.result()

            print("\n" + "=" * 60)
            print(" ✨ TEMPORAL WORKFLOW EXECUTION COMPLETED")
            print("=" * 60)
            print(f" Status:             {result['status']}")
            print(f" Approver:           {result['approver']}")
            print(f" Gold Checksum SHA:  {result['gold_manifest']['checksum_sha256']}")
            print(f" Chunks Indexed:     {result['gold_manifest']['chunk_count']}")
            print(f" Evaluation Status:  {result['evaluation']['eval_status']}")
            print("=" * 60 + "\n")
            return result


def main():
    asyncio.run(run_local_durable_sync())


if __name__ == "__main__":
    main()
