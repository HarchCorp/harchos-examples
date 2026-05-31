#!/usr/bin/env python3
"""Billing history viewer for HarchOS GPU workloads.

Retrieves and displays billing records from the HarchOS platform using
the Python SDK. Shows how to filter records by status, date range, and
compute spending summaries.

Features:
- List billing records with filters
- Filter by status (open, closed, paid, overdue)
- Date range filtering
- Spending summary with totals by status and currency
- Overdue record alerts

Usage:
    python billing_history.py
    python billing_history.py --status overdue
    python billing_history.py --last-30-days
    HARCHOS_API_KEY=hsk_... python billing_history.py
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOS
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated billing data")


# ---------------------------------------------------------------------------
# Simulated billing data (for local testing)
# ---------------------------------------------------------------------------

SIMULATED_RECORDS = [
    {
        "id": "bill-001",
        "user_id": "user-alice",
        "workload_id": "wkld-training-resnet",
        "hub_id": "hub-ouarzazate",
        "gpu_hours": 192.0,
        "cpu_core_hours": 768.0,
        "memory_gb_hours": 3072.0,
        "storage_gb_months": 50.0,
        "total_cost": 403.20,
        "currency": "USD",
        "status": "paid",
        "period_start": "2025-01-01T00:00:00Z",
        "period_end": "2025-01-31T23:59:59Z",
    },
    {
        "id": "bill-002",
        "user_id": "user-alice",
        "workload_id": "wkld-llama-inference",
        "hub_id": "hub-dakhla",
        "gpu_hours": 720.0,
        "cpu_core_hours": 1440.0,
        "memory_gb_hours": 5760.0,
        "storage_gb_months": 200.0,
        "total_cost": 1008.00,
        "currency": "USD",
        "status": "paid",
        "period_start": "2025-01-01T00:00:00Z",
        "period_end": "2025-01-31T23:59:59Z",
    },
    {
        "id": "bill-003",
        "user_id": "user-bob",
        "workload_id": "wkld-finetune-mistral",
        "hub_id": "hub-benguerir",
        "gpu_hours": 336.0,
        "cpu_core_hours": 1344.0,
        "memory_gb_hours": 5376.0,
        "storage_gb_months": 100.0,
        "total_cost": 789.60,
        "currency": "USD",
        "status": "open",
        "period_start": "2025-02-01T00:00:00Z",
        "period_end": "2025-02-28T23:59:59Z",
    },
    {
        "id": "bill-004",
        "user_id": "user-carol",
        "workload_id": "wkld-rag-pipeline",
        "hub_id": "hub-tanger",
        "gpu_hours": 48.0,
        "cpu_core_hours": 192.0,
        "memory_gb_hours": 768.0,
        "storage_gb_months": 500.0,
        "total_cost": 86.40,
        "currency": "USD",
        "status": "overdue",
        "period_start": "2024-12-01T00:00:00Z",
        "period_end": "2024-12-31T23:59:59Z",
    },
    {
        "id": "bill-005",
        "user_id": "user-alice",
        "workload_id": "wkld-etl-pipeline",
        "hub_id": "hub-ouarzazate",
        "gpu_hours": 0.0,
        "cpu_core_hours": 2000.0,
        "memory_gb_hours": 4000.0,
        "storage_gb_months": 1000.0,
        "total_cost": 210.00,
        "currency": "MAD",
        "status": "closed",
        "period_start": "2025-01-15T00:00:00Z",
        "period_end": "2025-02-14T23:59:59Z",
    },
]


class SimulatedBillingClient:
    """Simulated billing client for local testing."""

    def list_billing_records(self, **filters):
        """Return simulated billing records, applying filters."""
        records = SIMULATED_RECORDS
        if filters.get("status"):
            records = [r for r in records if r["status"] == filters["status"]]
        return records


# ---------------------------------------------------------------------------
# Billing History Viewer
# ---------------------------------------------------------------------------

class BillingHistoryViewer:
    """Retrieves and analyzes billing history from HarchOS."""

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOS(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = SimulatedBillingClient()

    def get_records(
        self,
        status: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Fetch billing records with optional filters."""
        try:
            if HARCHOS_AVAILABLE:
                records = self.client.pricing.list_billing_records(
                    status=status,
                    period_start=period_start,
                    period_end=period_end,
                    limit=limit,
                )
                # Convert SDK models to dicts for display
                return [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "workload_id": r.workload_id,
                        "hub_id": r.hub_id,
                        "gpu_hours": r.gpu_hours,
                        "cpu_core_hours": r.cpu_core_hours,
                        "memory_gb_hours": r.memory_gb_hours,
                        "storage_gb_months": r.storage_gb_months,
                        "total_cost": r.total_cost,
                        "currency": r.currency,
                        "status": r.status,
                        "period_start": str(r.period_start),
                        "period_end": str(r.period_end),
                    }
                    for r in records
                ]
            else:
                return self.client.list_billing_records(
                    status=status,
                    period_start=period_start,
                    period_end=period_end,
                )
        except Exception as e:
            print(f"[ERROR] Failed to retrieve billing records: {e}")
            return []

    def print_records(self, records: List[dict]):
        """Pretty-print billing records in a table format."""
        if not records:
            print("\n  No billing records found.")
            return

        print(f"\n  {'ID':12s} | {'Workload':28s} | {'Hub':18s} | {'GPU hrs':>8s} | "
              f"{'Total':>10s} | {'Currency':8s} | {'Status':8s}")
        print("  " + "-" * 110)

        for r in records:
            status_icon = {
                "paid": "✅",
                "open": "🟡",
                "closed": "🔵",
                "overdue": "🔴",
            }.get(r["status"], "⚪")

            print(f"  {r['id']:12s} | {(r.get('workload_id') or 'N/A'):28s} | "
                  f"{(r.get('hub_id') or 'N/A'):18s} | "
                  f"{r['gpu_hours']:8.1f} | "
                  f"{r['total_cost']:10.2f} | {r['currency']:8s} | "
                  f"{status_icon} {r['status']}")

    def compute_summary(self, records: List[dict]) -> dict:
        """Compute spending summary from billing records."""
        summary: Dict[str, dict] = {}

        for r in records:
            currency = r["currency"]
            if currency not in summary:
                summary[currency] = {
                    "total": 0.0,
                    "by_status": {},
                    "total_gpu_hours": 0.0,
                    "record_count": 0,
                }

            summary[currency]["total"] += r["total_cost"]
            summary[currency]["total_gpu_hours"] += r["gpu_hours"]
            summary[currency]["record_count"] += 1

            status = r["status"]
            if status not in summary[currency]["by_status"]:
                summary[currency]["by_status"][status] = 0.0
            summary[currency]["by_status"][status] += r["total_cost"]

        return summary

    def print_summary(self, summary: dict):
        """Pretty-print spending summary."""
        print("\n  📊 Spending Summary")
        print("  " + "=" * 50)

        for currency, data in summary.items():
            print(f"\n  Currency: {currency}")
            print(f"    Total spent:      {data['total']:>10.2f} {currency}")
            print(f"    Total GPU hours:  {data['total_gpu_hours']:>10.1f} hrs")
            print(f"    Record count:     {data['record_count']:>10d}")

            print(f"    By status:")
            for status, amount in data["by_status"].items():
                icon = {"paid": "✅", "open": "🟡", "closed": "🔵", "overdue": "🔴"}.get(status, "⚪")
                print(f"      {icon} {status:10s}: {amount:>10.2f} {currency}")

            # Alert on overdue
            overdue = data["by_status"].get("overdue", 0)
            if overdue > 0:
                print(f"\n    ⚠️  OVERDUE: {overdue:.2f} {currency} requires immediate attention!")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Billing History")
    parser.add_argument("--status", type=str, default=None,
                        choices=["open", "closed", "paid", "overdue"],
                        help="Filter by billing status")
    parser.add_argument("--last-30-days", action="store_true",
                        help="Show records from the last 30 days")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum number of records")
    args = parser.parse_args()

    viewer = BillingHistoryViewer()

    # Parse date range
    period_start = None
    period_end = None
    if args.last_30_days:
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=30)

    print("=" * 60)
    print("HarchOS Billing History")
    print("=" * 60)

    # Fetch records
    records = viewer.get_records(
        status=args.status,
        period_start=period_start,
        period_end=period_end,
        limit=args.limit,
    )

    # Display records
    viewer.print_records(records)

    # Compute and display summary
    if records:
        summary = viewer.compute_summary(records)
        viewer.print_summary(summary)

    print()


if __name__ == "__main__":
    main()
