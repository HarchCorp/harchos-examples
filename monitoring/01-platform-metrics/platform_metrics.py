#!/usr/bin/env python3
"""Platform-wide metrics display for HarchOS.

Fetches and displays aggregate metrics from the HarchOS Monitoring API,
including GPU utilization, energy consumption, carbon impact, and
infrastructure health indicators.

Features:
- Platform-wide GPU utilization and availability
- Energy consumption and renewable percentage
- Carbon intensity and CO2 savings
- Workload statistics
- Health categorization (low/moderate/high/critical)

Usage:
    python platform_metrics.py
    python platform_metrics.py --watch
    python platform_metrics.py --interval 60
    HARCHOS_API_KEY=hsk_... python platform_metrics.py
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

try:
    from harchos import HarchOS
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated metrics")


# ---------------------------------------------------------------------------
# Simulated metrics (for local testing)
# ---------------------------------------------------------------------------

SIMULATED_METRICS = {
    "total_hubs": 5,
    "total_gpus": 1798,
    "available_gpus": 423,
    "gpu_utilization_percent": 76.5,
    "total_workloads": 1247,
    "active_workloads": 89,
    "total_energy_kwh": 345678.5,
    "avg_renewable_percentage": 81.52,
    "avg_carbon_intensity": 47.0,
    "avg_pue": 1.12,
    "total_co2_saved_kg": 12456.3,
}


class SimulatedMonitoringClient:
    """Simulated monitoring client for local testing."""

    def metrics(self):
        """Return simulated platform metrics."""
        return SIMULATED_METRICS


# ---------------------------------------------------------------------------
# Metrics Display
# ---------------------------------------------------------------------------

class PlatformMetricsDisplay:
    """Displays and formats HarchOS platform metrics."""

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOS(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = SimulatedMonitoringClient()

    def fetch_metrics(self) -> dict:
        """Fetch platform metrics."""
        try:
            if HARCHOS_AVAILABLE:
                m = self.client.monitoring.metrics()
                return {
                    "total_hubs": m.total_hubs,
                    "total_gpus": m.total_gpus,
                    "available_gpus": m.available_gpus,
                    "gpu_utilization_percent": m.gpu_utilization_percent,
                    "total_workloads": m.total_workloads,
                    "active_workloads": m.active_workloads,
                    "total_energy_kwh": m.total_energy_kwh,
                    "avg_renewable_percentage": m.avg_renewable_percentage,
                    "avg_carbon_intensity": m.avg_carbon_intensity,
                    "avg_pue": m.avg_pue,
                    "total_co2_saved_kg": m.total_co2_saved_kg,
                    "utilization_health": m.utilization_health,
                }
            else:
                return self.client.metrics()
        except Exception as e:
            print(f"[ERROR] Failed to fetch metrics: {e}")
            return {}

    def print_metrics(self, metrics: dict):
        """Pretty-print platform metrics."""
        if not metrics:
            print("  No metrics available.")
            return

        # GPU Infrastructure
        total = metrics.get("total_gpus", 0)
        available = metrics.get("available_gpus", 0)
        used = total - available
        util = metrics.get("gpu_utilization_percent", 0)
        health = metrics.get("utilization_health", self._categorize_utilization(util))

        health_icon = {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}.get(health, "⚪")

        print("\n  ╔══════════════════════════════════════════════════════════╗")
        print("  ║              HarchOS Platform Metrics                   ║")
        print("  ╚══════════════════════════════════════════════════════════╝")

        print(f"\n  🖥️  GPU Infrastructure")
        print(f"  {'─' * 50}")
        print(f"    Total Hubs:          {metrics.get('total_hubs', 0):>8d}")
        print(f"    Total GPUs:          {total:>8d}")
        print(f"    Available GPUs:      {available:>8d}")
        print(f"    In-Use GPUs:         {used:>8d}")
        print(f"    Utilization:         {util:>7.1f}%  {health_icon} {health}")
        self._print_bar(util, 100)

        # Workloads
        print(f"\n  📋 Workloads")
        print(f"  {'─' * 50}")
        print(f"    Total Created:       {metrics.get('total_workloads', 0):>8d}")
        print(f"    Currently Active:    {metrics.get('active_workloads', 0):>8d}")

        # Energy & Carbon
        energy = metrics.get("total_energy_kwh", 0)
        renewable = metrics.get("avg_renewable_percentage", 0)
        carbon = metrics.get("avg_carbon_intensity", 0)
        pue = metrics.get("avg_pue", 0)
        co2_saved = metrics.get("total_co2_saved_kg", 0)

        print(f"\n  ⚡ Energy & Carbon")
        print(f"  {'─' * 50}")
        print(f"    Total Energy:        {energy:>10,.1f} kWh")
        print(f"    Renewable Share:     {renewable:>7.1f}%")
        self._print_bar(renewable, 100, fill_char="🌱")
        print(f"    Avg Carbon Intensity:{carbon:>7.1f} gCO2/kWh")
        carbon_icon = "🟢" if carbon <= 100 else ("🟡" if carbon <= 200 else "🔴")
        print(f"    Carbon Rating:       {carbon_icon}")
        print(f"    Avg PUE:             {pue:>7.2f}")
        pue_rating = "Excellent" if pue <= 1.2 else ("Good" if pue <= 1.5 else "Needs Improvement")
        print(f"    PUE Rating:          {pue_rating}")
        print(f"    CO2 Saved:           {co2_saved:>10,.1f} kg")
        print(f"    CO2 Saved (tonnes):  {co2_saved / 1000:>10,.2f} t")

    def _categorize_utilization(self, pct: float) -> str:
        """Categorize GPU utilization level."""
        if pct >= 90:
            return "critical"
        elif pct >= 75:
            return "high"
        elif pct >= 50:
            return "moderate"
        else:
            return "low"

    def _print_bar(self, value: float, max_val: float, width: int = 30, fill_char: str = "█"):
        """Print a simple progress bar."""
        pct = min(value / max_val, 1.0)
        filled = int(pct * width)
        empty = width - filled
        print(f"    [{fill_char * filled}{'░' * empty}] {pct * 100:.1f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Platform Metrics")
    parser.add_argument("--watch", action="store_true",
                        help="Continuously watch metrics")
    parser.add_argument("--interval", type=int, default=30,
                        help="Refresh interval in seconds (default: 30)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    display = PlatformMetricsDisplay()

    if args.watch:
        print("Watching platform metrics (Ctrl+C to stop)...")
        try:
            while True:
                metrics = display.fetch_metrics()
                if args.json:
                    print(json.dumps(metrics, indent=2))
                else:
                    # Clear screen for refresh
                    print("\033[2J\033[H", end="")
                    display.print_metrics(metrics)
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"\n  Last updated: {ts} | Next refresh in {args.interval}s")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped watching.")
    else:
        print("=" * 60)
        print("HarchOS Platform Metrics")
        print("=" * 60)

        metrics = display.fetch_metrics()

        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            display.print_metrics(metrics)
            print()


if __name__ == "__main__":
    main()
