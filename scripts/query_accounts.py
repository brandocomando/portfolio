#!/usr/bin/env python3
"""Query Google Cloud Firestore database for user accounts created over a time period.

Usage:
    python scripts/query_accounts.py [--since 24h]
    python scripts/query_accounts.py --since 7d
    python scripts/query_accounts.py --since 30d --raw
"""

import sys
import os
import re
import json
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

DEFAULT_PROJECT = os.getenv("GCP_PROJECT_ID", "portfolio-510722")
DEFAULT_COLLECTION = os.getenv("FIRESTORE_COLLECTION_LEADS", "portfolio_leads")


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


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parses an ISO format datetime string into a timezone-aware UTC datetime."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def get_firestore_client(project: str):
    """Initializes Firestore client, gracefully using gcloud access token or ADC credentials."""
    from google.cloud import firestore

    # 1. If explicit credentials path is specified in environment, use ADC
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            import google.auth
            creds, _ = google.auth.default()
            return firestore.Client(project=project, credentials=creds)
        except Exception:
            pass

    # 2. Use authenticated gcloud session (fast and reliable in local dev)
    try:
        import google.oauth2.credentials
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            stderr=subprocess.PIPE
        ).decode().strip()
        creds = google.oauth2.credentials.Credentials(token)
        return firestore.Client(project=project, credentials=creds)
    except Exception:
        pass

    # 3. Fallback to standard Google Auth
    try:
        import google.auth
        creds, _ = google.auth.default()
        return firestore.Client(project=project, credentials=creds)
    except Exception as e:
        print(f"Error initializing Firestore client for project '{project}': {e}", file=sys.stderr)
        sys.exit(1)


def get_account_creation_time(doc, data: Dict[str, Any]) -> Optional[datetime]:
    """Determines the account creation datetime from document data or Firestore snapshot metadata."""
    # 1. Check explicit created_at field
    if data.get("created_at"):
        dt = parse_iso_datetime(data["created_at"])
        if dt:
            return dt

    # 2. Check first_login field
    if data.get("first_login"):
        dt = parse_iso_datetime(data["first_login"])
        if dt:
            return dt

    # 3. Check Firestore document snapshot create_time metadata
    if hasattr(doc, "create_time") and doc.create_time:
        ct = doc.create_time
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
        return ct

    # 4. Fallback to last_login or last_active
    for key in ["last_login", "last_active"]:
        if data.get(key):
            dt = parse_iso_datetime(data[key])
            if dt:
                return dt

    return None


def main():
    parser = argparse.ArgumentParser(description="Query Firestore DB for newly created accounts.")
    parser.add_argument("--since", default="24h", help="Time range (e.g. 24h, 1d, 7d, 30d; default: 24h)")
    parser.add_argument("--start", default=None, help="Explicit start ISO timestamp (e.g. 2026-10-12T00:00:00Z)")
    parser.add_argument("--end", default=None, help="Explicit end ISO timestamp (e.g. 2026-10-13T00:00:00Z)")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help=f"GCP Project ID (default: {DEFAULT_PROJECT})")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help=f"Firestore collection name (default: {DEFAULT_COLLECTION})")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON array")

    args = parser.parse_args()

    now_utc = datetime.now(timezone.utc)
    if args.start:
        start_time = parse_iso_datetime(args.start)
        if not start_time:
            print(f"Invalid start timestamp: {args.start}", file=sys.stderr)
            sys.exit(1)
    else:
        duration = parse_since(args.since)
        start_time = now_utc - duration

    end_time = parse_iso_datetime(args.end) if args.end else now_utc

    db = get_firestore_client(args.project)

    try:
        docs = list(db.collection(args.collection).stream())
    except Exception as e:
        print(f"Failed to query Firestore collection '{args.collection}': {e}", file=sys.stderr)
        sys.exit(1)

    matching_accounts = []
    for doc in docs:
        data = doc.to_dict() or {}
        created_dt = get_account_creation_time(doc, data)

        if created_dt and start_time <= created_dt <= end_time:
            matching_accounts.append({
                "uid": doc.id,
                "email": data.get("email"),
                "name": data.get("name"),
                "provider": data.get("provider", "unknown"),
                "created_at": created_dt.isoformat(),
                "last_login": data.get("last_login"),
                "last_active": data.get("last_active"),
                "client_ip": data.get("client_ip"),
                "login_count": data.get("login_count", 1),
                "_created_dt": created_dt
            })

    # Sort descending by creation date
    matching_accounts.sort(key=lambda x: x["_created_dt"], reverse=True)

    if args.raw:
        for acc in matching_accounts:
            acc.pop("_created_dt", None)
        print(json.dumps(matching_accounts, indent=2))
        return

    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 80)
    print(f"Firestore DB Accounts [{args.collection}]")
    print(f"Time Range: {start_str} to {end_str} (past {args.since})")
    print(f"Project:    {args.project}")
    print("=" * 80)

    if not matching_accounts:
        print(f"\nNo accounts were created during this time period (past {args.since}).")
        print(f"Total registered accounts currently in collection '{args.collection}': {len(docs)}")
        print(f"Tip: To check a wider time range, run: task accounts SINCE=7d (or task firestore:accounts SINCE=30d)\n")
        return

    for idx, acc in enumerate(matching_accounts, 1):
        created_display = parse_iso_datetime(acc["created_at"]).strftime("%Y-%m-%d %H:%M:%S UTC")
        name_display = acc.get("name") or "(No Name)"
        email_display = acc.get("email") or "(No Email)"
        print(f"\n[{idx}] User: {name_display} <{email_display}>")
        print(f"    UID:          {acc['uid']}")
        print(f"    Provider:     {acc['provider']}")
        print(f"    Created At:   {created_display}")
        print(f"    Last Active:  {acc.get('last_active') or acc.get('last_login') or 'N/A'}")
        print(f"    Client IP:    {acc.get('client_ip') or 'N/A'}")
        print(f"    Login Count:  {acc.get('login_count', 1)}")

    print("\n" + "-" * 80)
    print(f"Found {len(matching_accounts)} new account(s) created in past {args.since}.")
    print(f"Total registered accounts in collection '{args.collection}': {len(docs)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
