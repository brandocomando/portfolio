#!/usr/bin/env python3
"""Query Google Cloud Logging or local logs for backend service activity and visitor questions.

Usage:
    python scripts/query_logs.py [--since 24h] [--questions-only] [--limit 500]
    python scripts/query_logs.py --since 7d --questions-only
    python scripts/query_logs.py --file /path/to/logfile.log --questions-only
"""

import sys
import os
import re
import json
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

DEFAULT_SERVICE = os.getenv("CLOUD_RUN_SERVICE", "portfolio-backend-prod")
DEFAULT_PROJECT = os.getenv("GCP_PROJECT_ID", "portfolio-510722")


def parse_since(since_str: str) -> timedelta:
    """Parses duration strings like '24h', '1d', '30m', '7d', or raw hours like '24' into a timedelta."""
    s = since_str.strip().lower()
    if s.endswith("h") or s.endswith("hr") or s.endswith("hours"):
        val = int(re.match(r"^\d+", s).group(0))
        return timedelta(hours=val)
    elif s.endswith("d") or s.endswith("day") or s.endswith("days"):
        val = int(re.match(r"^\d+", s).group(0))
        return timedelta(days=val)
    elif s.endswith("m") or s.endswith("min") or s.endswith("minutes"):
        val = int(re.match(r"^\d+", s).group(0))
        return timedelta(minutes=val)
    elif s.isdigit():
        return timedelta(hours=int(s))
    return timedelta(hours=24)


def fetch_cloud_logs(
    project: str,
    service: str,
    since: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 1000,
    questions_only: bool = False
) -> List[Dict[str, Any]]:
    """Fetches Cloud Run logs using the authenticated gcloud CLI."""
    filter_parts = [
        'resource.type="cloud_run_revision"',
        f'resource.labels.service_name="{service}"'
    ]

    if questions_only:
        filter_parts.append(
            '("Question asked" OR "Anonymous interaction" OR "Question Asked" OR "CONTACT MESSAGE FORWARDED")'
        )

    cmd = [
        "gcloud", "logging", "read",
        " AND ".join(filter_parts),
        f"--project={project}",
        f"--limit={limit}",
        "--order=desc",
        "--format=json"
    ]

    if start:
        cmd[3] += f' AND timestamp >= "{start}"'
    if end:
        cmd[3] += f' AND timestamp <= "{end}"'
    if not start and not end:
        # Normalize freshness flag for gcloud
        freshness = since
        if freshness.isdigit():
            freshness = f"{freshness}h"
        cmd.append(f"--freshness={freshness}")

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        entries = json.loads(res.stdout) if res.stdout.strip() else []
        # Return in chronological order
        return sorted(entries, key=lambda x: x.get("timestamp", ""))
    except subprocess.CalledProcessError as e:
        print(f"Error fetching logs from Google Cloud Logging: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing gcloud log output: {e}", file=sys.stderr)
        return []


def read_file_logs(file_path: str) -> List[Dict[str, Any]]:
    """Reads logs from a local text or JSON log file."""
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        return []

    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("{") and line_str.endswith("}"):
                try:
                    data = json.loads(line_str)
                    entries.append(data)
                    continue
                except Exception:
                    pass
            entries.append({"textPayload": line_str, "timestamp": ""})
    return entries


def extract_question_info(log_text: str) -> Optional[Dict[str, str]]:
    """Extracts requester and question content from log text if present."""
    # Pattern 1: New standardized log format: Question asked [via ...] by <requester>: <question>
    m1 = re.search(
        r"Question (?:asked|submitted)(?: via [^:]+)? by (?P<requester>.+?\)|[^:]+):\s*(?P<question>.+)",
        log_text,
        re.IGNORECASE
    )
    if m1:
        return {
            "requester": m1.group("requester").strip(),
            "question": m1.group("question").strip()
        }

    # Pattern 2: Historical anonymous interaction: Anonymous interaction from <ip>: '<question>'
    m2 = re.search(r"Anonymous interaction from (?P<requester>[^:]+):\s*['\"](?P<question>.+?)['\"]", log_text)
    if m2:
        return {
            "requester": f"anonymous IP '{m2.group('requester').strip()}'",
            "question": m2.group("question").strip()
        }

    # Pattern 3: Webhook notification: Question Asked: "*<question>*"
    m3 = re.search(r"Question Asked:\s*[\*\"'](?P<question>.+?)[\*\"']", log_text)
    if m3:
        return {
            "requester": "user (from notification)",
            "question": m3.group("question").strip()
        }

    # Pattern 4: Contact message log
    m4 = re.search(r"CONTACT MESSAGE FORWARDED: from='(?P<email>[^']+)'[^:]*:\s*(?P<question>.+)", log_text)
    if m4:
        return {
            "requester": f"contact from '{m4.group('email').strip()}'",
            "question": m4.group("question").strip()
        }

    return None


def extract_trace_id(text: str, entry: Dict[str, Any]) -> Optional[str]:
    """Extracts trace ID from log text or Cloud Logging entry metadata."""
    m = re.search(r"trace_id=([^\s\]]+)", text)
    if m and m.group(1) != "no-trace":
        return m.group(1)
    trace = entry.get("trace")
    if trace:
        return trace.split("/")[-1]
    return None


def format_timestamp(ts_str: str) -> str:
    """Formats an ISO timestamp into readable UTC string."""
    if not ts_str:
        return "UNKNOWN_TIME"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ts_str


def main():
    parser = argparse.ArgumentParser(description="Query logs and extract visitor questions.")
    parser.add_argument("--since", default="24h", help="Time range (e.g. 24h, 1d, 7d, 30m; default: 24h)")
    parser.add_argument("--start", default=None, help="Start ISO timestamp (e.g. 2026-10-12T00:00:00Z)")
    parser.add_argument("--end", default=None, help="End ISO timestamp (e.g. 2026-10-13T00:00:00Z)")
    parser.add_argument("--questions-only", action="store_true", help="Filter and display only questions asked")
    parser.add_argument("--service", default=DEFAULT_SERVICE, help=f"Cloud Run service name (default: {DEFAULT_SERVICE})")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help=f"GCP project ID (default: {DEFAULT_PROJECT})")
    parser.add_argument("--limit", type=int, default=1000, help="Max log records to fetch (default: 1000)")
    parser.add_argument("--file", default=None, help="Optional local log file to parse instead of Cloud Logging")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON log records")

    args = parser.parse_args()

    if args.file:
        entries = read_file_logs(args.file)
        source_desc = f"local file: {args.file}"
    else:
        entries = fetch_cloud_logs(
            project=args.project,
            service=args.service,
            since=args.since,
            start=args.start,
            end=args.end,
            limit=args.limit,
            questions_only=args.questions_only
        )
        source_desc = f"Cloud Run '{args.service}' in project '{args.project}'"

    if args.raw:
        print(json.dumps(entries, indent=2))
        return

    if args.questions_only:
        print("=" * 80)
        print(f"Backend API Questions [{args.since}]")
        print(f"Source: {source_desc}")
        print("=" * 80)

        questions = []
        seen_traces = set()
        seen_recent = []

        for entry in entries:
            text = entry.get("textPayload") or json.dumps(entry.get("jsonPayload", {}))
            q_info = extract_question_info(text)
            if not q_info:
                continue

            trace_id = extract_trace_id(text, entry)
            if trace_id and trace_id in seen_traces:
                continue

            raw_ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")) if raw_ts else None
            except Exception:
                dt = None

            # Deduplicate identical (requester, question) within 30 seconds (e.g. stream start vs stream end background task)
            requester = q_info["requester"]
            question = q_info["question"]
            is_dup = False
            if dt:
                for prev_dt, prev_req, prev_q in seen_recent[-10:]:
                    if prev_req == requester and prev_q == question and abs((dt - prev_dt).total_seconds()) <= 30:
                        is_dup = True
                        break

            if is_dup:
                continue

            if trace_id:
                seen_traces.add(trace_id)
            if dt:
                seen_recent.append((dt, requester, question))

            ts = format_timestamp(raw_ts)
            questions.append({
                "timestamp": ts,
                "requester": requester,
                "question": question
            })

        if not questions:
            print(f"\nNo questions found in logs over the specified time range (past {args.since}).")
            print(f"Total log records analyzed: {len(entries)}")
            print("Tip: Check a wider time range using: task questions SINCE=7d\n")
            return

        for idx, q in enumerate(questions, 1):
            print(f"\n[{idx}] {q['timestamp']}")
            print(f"    Whom:     {q['requester']}")
            print(f"    Question: {q['question']}")

        print("\n" + "-" * 80)
        print(f"Total questions asked: {len(questions)} (out of {len(entries)} total log records)")
        print("=" * 80)
    else:
        print("=" * 80)
        print(f"Backend API Logs [{args.since}]")
        print(f"Source: {source_desc}")
        print("=" * 80)

        if not entries:
            print(f"\nNo log entries found for past {args.since}.")
            print("Tip: Check a wider time range using: task logs SINCE=7d\n")
            return

        for entry in entries:
            ts = format_timestamp(entry.get("timestamp", ""))
            payload = entry.get("textPayload")
            if not payload and "jsonPayload" in entry:
                payload = json.dumps(entry["jsonPayload"])
            severity = entry.get("severity", "INFO")
            print(f"[{ts}] [{severity}] {payload}")

        print("\n" + "-" * 80)
        print(f"Total log entries displayed: {len(entries)}")
        print("=" * 80)


if __name__ == "__main__":
    main()
