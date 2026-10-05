"""Integration tests for Temporal KnowledgeSyncWorkflow."""

import pytest
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

TASK_QUEUE = "test-mlops-queue"


@pytest.mark.asyncio
async def test_temporal_knowledge_sync_automated():
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
            handle = await env.client.start_workflow(
                KnowledgeSyncWorkflow.run,
                False, # require_manual_approval = False
                id="test-sync-auto",
                task_queue=TASK_QUEUE,
            )

            # Test Query
            status = await handle.query(KnowledgeSyncWorkflow.get_pipeline_status)
            assert "current_step" in status

            # Wait for execution
            result = await handle.result()
            assert result["status"] == "COMPLETED"
            assert result["evaluation"]["passed"] is True
            assert len(result["gold_manifest"]["checksum_sha256"]) == 64


@pytest.mark.asyncio
async def test_temporal_human_in_the_loop_signal():
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
            handle = await env.client.start_workflow(
                KnowledgeSyncWorkflow.run,
                True, # require_manual_approval = True
                id="test-sync-signal",
                task_queue=TASK_QUEUE,
            )

            # Send external approval signal
            await handle.signal(KnowledgeSyncWorkflow.approve_deployment, "lead-platform-architect-brandon")

            result = await handle.result()
            assert result["status"] == "COMPLETED"
            assert result["approver"] == "lead-platform-architect-brandon"
