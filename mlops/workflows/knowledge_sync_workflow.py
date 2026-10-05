"""Temporal Durable Workflow: KnowledgeSyncWorkflow.

Orchestrates the entire MLOps knowledge lifecycle with automatic retries,
checkpointing, real-time queries, and human-in-the-loop signals.
"""

from datetime import timedelta
from typing import Dict, Any, Optional
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from mlops.workflows.activities import (
        ingest_bronze_activity,
        transform_silver_activity,
        build_gold_activity,
        evaluate_benchmark_activity,
        publish_artifacts_activity,
    )


@workflow.defn
class KnowledgeSyncWorkflow:
    def __init__(self):
        self._current_step: str = "INITIALIZING"
        self._is_approved: bool = False
        self._approver: Optional[str] = None
        self._manifest: Optional[Dict[str, Any]] = None

    @workflow.query
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Query method: Exposes live execution state without altering workflow history."""
        return {
            "current_step": self._current_step,
            "is_approved": self._is_approved,
            "approver": self._approver,
            "manifest": self._manifest
        }

    @workflow.signal
    def approve_deployment(self, approver: str):
        """Signal method: Enables asynchronous human-in-the-loop deployment approvals."""
        workflow.logger.info(f"Received deployment approval signal from: {approver}")
        self._is_approved = True
        self._approver = approver

    @workflow.run
    async def run(self, require_manual_approval: bool = False) -> Dict[str, Any]:
        workflow.logger.info("Starting Durable KnowledgeSyncWorkflow Execution")

        # Standard retry policy for network and API I/O
        io_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3
        )

        # Step 1: Bronze Ingest
        self._current_step = "INGESTING_BRONZE"
        bronze_result = await workflow.execute_activity(
            ingest_bronze_activity,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=io_retry_policy
        )

        # Step 2: Silver Transform & Data Contracts
        self._current_step = "TRANSFORMING_SILVER"
        silver_result = await workflow.execute_activity(
            transform_silver_activity,
            start_to_close_timeout=timedelta(minutes=2)
        )

        # Step 3: Gold Index & Manifest Build
        self._current_step = "BUILDING_GOLD"
        gold_result = await workflow.execute_activity(
            build_gold_activity,
            start_to_close_timeout=timedelta(minutes=3)
        )
        self._manifest = gold_result

        # Step 4: Run Continuous Evaluation Benchmark Gate
        self._current_step = "RUNNING_EVALUATION"
        eval_result = await workflow.execute_activity(
            evaluate_benchmark_activity,
            start_to_close_timeout=timedelta(minutes=3)
        )

        if not eval_result.get("passed", False):
            self._current_step = "FAILED_EVALUATION"
            raise RuntimeError("Evaluation Benchmark Gate Failed: Retrieval accuracy or guardrail breached.")

        # Step 5: Human-in-the-Loop Gate (if configured or score is borderline)
        if require_manual_approval:
            self._current_step = "WAITING_HUMAN_APPROVAL"
            workflow.logger.info("Workflow paused: Awaiting human approval signal before publishing index...")
            await workflow.wait_condition(lambda: self._is_approved, timeout=timedelta(hours=24))
        else:
            self._is_approved = True
            self._approver = "automated-ci-eval-gate"

        # Step 6: Atomic Publish to Production
        self._current_step = "PUBLISHING_PRODUCTION"
        publish_result = await workflow.execute_activity(
            publish_artifacts_activity,
            gold_result,
            start_to_close_timeout=timedelta(minutes=1)
        )

        self._current_step = "COMPLETED"
        return {
            "status": "COMPLETED",
            "approver": self._approver,
            "gold_manifest": gold_result,
            "bronze": bronze_result,
            "silver": silver_result,
            "evaluation": eval_result,
            "publication": publish_result
        }
