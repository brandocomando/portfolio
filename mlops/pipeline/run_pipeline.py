"""Master MLOps Pipeline Orchestrator.

Executes Bronze Ingestion -> Silver Transformation & Quality Gates -> Gold Index Build.
"""

import sys
import argparse
from mlops.pipeline.ingest_sources import run_bronze_ingestion
from mlops.pipeline.transform_silver import run_silver_transform
from mlops.pipeline.build_gold_index import run_gold_build


def main():
    parser = argparse.ArgumentParser(description="Portfolio Knowledge MLOps Pipeline")
    parser.add_argument(
        "--stage",
        choices=["bronze", "silver", "gold", "all"],
        default="all",
        help="Pipeline stage to execute (default: all)"
    )
    args = parser.parse_args()

    print(f"🚀 Starting MLOps Medallion Pipeline [Stage: {args.stage.upper()}]...")

    if args.stage in ["bronze", "all"]:
        print("\n=== STAGE 1: BRONZE RAW INGESTION ===")
        run_bronze_ingestion()

    if args.stage in ["silver", "all"]:
        print("\n=== STAGE 2: SILVER ENRICHMENT & DATA CONTRACT GATES ===")
        run_silver_transform()

    if args.stage in ["gold", "all"]:
        print("\n=== STAGE 3: GOLD HYBRID INDEX & SIGNED ARTIFACT BUILD ===")
        manifest = run_gold_build()
        print(f"\n✨ Pipeline execution complete! Gold artifact SHA: {manifest['checksum_sha256']}")


if __name__ == "__main__":
    main()
