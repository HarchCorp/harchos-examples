#!/usr/bin/env python3
"""Cross-region monitoring dashboard for HarchOS.

Builds a unified monitoring dashboard that combines data from the
monitoring, regions, and carbon APIs to provide a cross-region view
of platform health, GPU utilization, and carbon metrics.

Features:
- Cross-region health aggregation
- Per-region GPU utilization breakdown
- Carbon intensity heatmap across regions
- Real-time monitoring with --watch
- Sovereignty compliance status per region
- Alerting thresholds for GPU utilization and carbon

Usage:
    python monitoring_dashboard.py
    python monitoring_dashboard.py --watch
    python monitoring_dashboard.py --interval 60
    HARCHOS_API_KEY=hsk_... python monitoring_dashboard.py
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOSClient
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated monitoring data")


# ---------------------------------------------------------------------------
# Simulated data
# ---------------------------------------------------------------------------

SIMULATED_REGIONS = [
    {"name": "Morocco", "code": "morocco", "available": True,
     "hub_count": 5, "total_gpus": 1798, "available_gpus": 423,
     "avg_renewable_percentage": 81.52, "avg_carbon_intensity": 47.0,
     "latency_ms": 0, "compliance_frameworks": ["GDPR", "CNDP", "ISO27001"],
     "gpu_utilization": 76.5},
    {"name": "Nigeria", "code": "nigeria", "available": False,
     "hub_count": 0, "total_gpus": 0, "available_gpus": 0,
     "avg_renewable_percentage": 0, "avg_carbon_intensity": 0,
     "latency_ms": 85, "compliance_frameworks": ["NDPR", "GDPR"],
     "gpu_utilization": 0},
    {"name": "Kenya", "code": "kenya", "available": False,
     "hub_count": 0, "total_gpus": 0, "available_gpus": 0,
     "avg_renewable_percentage": 0, "avg_carbon_intensity": 0,
     "latency_ms": 120, "compliance_frameworks": ["PDPA", "GDPR"],
     "gpu_utilization": 0},
]

SIMULATED_HUBS = [
    {"name": "Harch Ouarzazate", "region": "morocco", "gpus": 800,
     "available_gpus": 180, "utilization": 77.5, "carbon_intensity": 18,
     "renewable_pct": 97.2, "status": "healthy", "workloads": 45},
    {"name": "Harch Dakhla", "region": "morocco", "gpus": 400,
     "available_gpus": 95, "utilization": 76.3, "carbon_intensity": 32,
     "renewable_pct": 94.8, "status": "healthy", "workloads": 22},
    {"name": "Harch Benguerir", "region": "morocco", "gpus": 350,
     "available_gpus": 82, "utilization": 76.6, "carbon_intensity": 55,
     "renewable_pct": 88.5, "status": "healthy", "workloads": 18},
    {"name": "Harch Tanger", "region": "morocco", "gpus": 200,
     "available_gpus": 48, "utilization": 76.0, "carbon_intensity": 95,
     "renewable_pct": 82.1, "status": "healthy", "workloads": 8},
    {"name": "Harch Casablanca", "region": "morocco", "gpus": 48,
     "available_gpus": 18, "utilization": 62.5, "carbon_intensity": 210,
     "renewable_pct": 45.0, "status": "degraded", "workloads": 3},
]

SIMULATED_HEALTH = {
    "status": "healthy",
    "database_status": "connected",
    "api_version": "0.2.0",
    "uptime_seconds": 86400 * 14 + 3600 * 6,
    "total_endpoints": 47,
    "active_connections": 128,
}


# ---------------------------------------------------------------------------
# Cross-Region Dashboard
# ---------------------------------------------------------------------------

class CrossRegionDashboard:
    """Unified monitoring dashboard across HarchOS regions."""

    # Alert thresholds
    GPU_UTIL_WARNING = 85.0
    GPU_UTIL_CRITICAL = 95.0
    CARBON_WARNING = 200.0
    CARBON_CRITICAL = 400.0

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOSClient(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = None

    def fetch_all_data(self) -> dict:
        """Fetch all data needed for the dashboard."""
        data = {
            "platform_health": SIMULATED_HEALTH,
            "regions": SIMULATED_REGIONS,
            "hubs": SIMULATED_HUBS,
            "alerts": [],
        }

        if self.client:
            try:
                health = self.client.monitoring.detailed_health()
                data["platform_health"] = {
                    "status": health.status,
                    "database_status": health.database_status,
                    "api_version": health.api_version,
                    "uptime_seconds": health.uptime_seconds,
                    "total_endpoints": health.total_endpoints,
                    "active_connections": health.active_connections,
                }
            except Exception:
                pass

            try:
                metrics = self.client.monitoring.metrics()
                data["platform_metrics"] = {
                    "total_hubs": metrics.total_hubs,
                    "total_gpus": metrics.total_gpus,
                    "available_gpus": metrics.available_gpus,
                    "gpu_utilization_percent": metrics.gpu_utilization_percent,
                    "active_workloads": metrics.active_workloads,
                    "avg_renewable_percentage": metrics.avg_renewable_percentage,
                    "avg_carbon_intensity": metrics.avg_carbon_intensity,
                    "total_co2_saved_kg": metrics.total_co2_saved_kg,
                }
            except Exception:
                pass

            try:
                regions = self.client.regions.list()
                data["regions"] = [
                    {
                        "name": r.name, "code": r.code, "available": r.available,
                        "hub_count": r.hub_count, "total_gpus": r.total_gpus,
                        "avg_renewable_percentage": r.avg_renewable_percentage,
                        "avg_carbon_intensity": r.avg_carbon_intensity,
                        "compliance_frameworks": r.compliance_frameworks,
                    }
                    for r in regions
                ]
            except Exception:
                pass

        # Compute alerts
        data["alerts"] = self._compute_alerts(data)
        return data

    def _compute_alerts(self, data: dict) -> List[dict]:
        """Compute alert conditions from monitoring data."""
        alerts = []

        # Platform health alerts
        health = data.get("platform_health", {})
        if health.get("status") != "healthy":
            alerts.append({
                "level": "critical" if health.get("status") == "unhealthy" else "warning",
                "source": "platform",
                "message": f"Platform status: {health.get('status', 'unknown')}",
            })

        if health.get("database_status") != "connected":
            alerts.append({
                "level": "critical",
                "source": "database",
                "message": f"Database: {health.get('database_status', 'unknown')}",
            })

        # Hub-level alerts
        for hub in data.get("hubs", []):
            if hub["utilization"] >= self.GPU_UTIL_CRITICAL:
                alerts.append({
                    "level": "critical",
                    "source": hub["name"],
                    "message": f"GPU utilization critical: {hub['utilization']:.1f}%",
                })
            elif hub["utilization"] >= self.GPU_UTIL_WARNING:
                alerts.append({
                    "level": "warning",
                    "source": hub["name"],
                    "message": f"GPU utilization high: {hub['utilization']:.1f}%",
                })

            if hub["carbon_intensity"] >= self.CARBON_CRITICAL:
                alerts.append({
                    "level": "critical",
                    "source": hub["name"],
                    "message": f"Carbon intensity critical: {hub['carbon_intensity']} gCO2/kWh",
                })
            elif hub["carbon_intensity"] >= self.CARBON_WARNING:
                alerts.append({
                    "level": "warning",
                    "source": hub["name"],
                    "message": f"Carbon intensity high: {hub['carbon_intensity']} gCO2/kWh",
                })

            if hub.get("status") != "healthy":
                alerts.append({
                    "level": "warning",
                    "source": hub["name"],
                    "message": f"Hub status: {hub.get('status', 'unknown')}",
                })

        return alerts

    def render_dashboard(self, data: dict):
        """Render the cross-region monitoring dashboard."""
        health = data["platform_health"]
        regions = data["regions"]
        hubs = data["hubs"]
        alerts = data["alerts"]
        metrics = data.get("platform_metrics", {})

        # Header
        status_icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
            health.get("status", "unknown"), "❓")

        uptime_days = health.get("uptime_seconds", 0) / 86400
        uptime_hours = (health.get("uptime_seconds", 0) % 86400) / 3600

        print("\n  ╔════════════════════════════════════════════════════════════════════╗")
        print("  ║          HarchOS Cross-Region Monitoring Dashboard                ║")
        print("  ╚════════════════════════════════════════════════════════════════════╝")

        print(f"\n  🏥 Platform Health: {status_icon} {health.get('status', 'unknown').upper()}")
        print(f"  {'─' * 70}")
        print(f"    API Version:      {health.get('api_version', 'N/A')}")
        print(f"    Uptime:           {int(uptime_days)}d {int(uptime_hours)}h")
        print(f"    Database:         {'✅ Connected' if health.get('database_status') == 'connected' else '❌ ' + health.get('database_status', 'N/A')}")
        print(f"    Endpoints:        {health.get('total_endpoints', 0)}")
        print(f"    Active Conns:     {health.get('active_connections', 0)}")

        # Platform metrics summary
        if metrics:
            print(f"\n  📊 Platform Summary")
            print(f"  {'─' * 70}")
            print(f"    Total Hubs:       {metrics.get('total_hubs', 0)}")
            print(f"    Total GPUs:       {metrics.get('total_gpus', 0)}")
            print(f"    Available GPUs:   {metrics.get('available_gpus', 0)}")
            print(f"    GPU Utilization:  {metrics.get('gpu_utilization_percent', 0):.1f}%")
            print(f"    Active Workloads: {metrics.get('active_workloads', 0)}")
            print(f"    Avg Renewable:    {metrics.get('avg_renewable_percentage', 0):.1f}%")
            print(f"    Avg Carbon:       {metrics.get('avg_carbon_intensity', 0):.1f} gCO2/kWh")
            print(f"    CO2 Saved:        {metrics.get('total_co2_saved_kg', 0):,.1f} kg")

        # Region overview
        print(f"\n  🌍 Regions ({len(regions)} total)")
        print(f"  {'─' * 70}")
        print(f"    {'Region':15s} | {'Status':10s} | {'Hubs':5s} | {'GPUs':6s} | "
              f"{'Renewable':9s} | {'Carbon':8s} | Compliance")
        print(f"    {'─' * 15}-+-{'─' * 10}-+-{'─' * 5}-+-{'─' * 6}-+-{'─' * 9}-+-{'─' * 8}-+-{'─' * 20}")

        for r in regions:
            status = "🟢 Active" if r["available"] else "⬜ Planned"
            carbon = f"{r['avg_carbon_intensity']:.0f}" if r["available"] else "N/A"
            renewable = f"{r['avg_renewable_percentage']:.1f}%" if r["available"] else "N/A"
            frameworks = ", ".join(r.get("compliance_frameworks", []))
            print(f"    {r['name']:15s} | {status:10s} | {r['hub_count']:5d} | "
                  f"{r['total_gpus']:6d} | {renewable:9s} | {carbon:8s} | {frameworks}")

        # Hub breakdown
        print(f"\n  🏭 Hub Details ({len(hubs)} hubs)")
        print(f"  {'─' * 70}")
        print(f"    {'Hub':22s} | {'GPUs':5s} | {'Avail':5s} | {'Util':6s} | "
              f"{'Carbon':8s} | {'Renew':6s} | Status")
        print(f"    {'─' * 22}-+-{'─' * 5}-+-{'─' * 5}-+-{'─' * 6}-+-{'─' * 8}-+-{'─' * 6}-+-{'─' * 8}")

        for hub in sorted(hubs, key=lambda h: h["carbon_intensity"]):
            carbon_icon = "🟢" if hub["carbon_intensity"] <= 100 else (
                "🟡" if hub["carbon_intensity"] <= 200 else "🔴")
            status_icon = "✅" if hub["status"] == "healthy" else "⚠️"
            print(f"    {hub['name']:22s} | {hub['gpus']:5d} | {hub['available_gpus']:5d} | "
                  f"{hub['utilization']:5.1f}% | {carbon_icon} {hub['carbon_intensity']:4d} | "
                  f"{hub['renewable_pct']:5.1f}% | {status_icon} {hub['status']}")

        # Alerts
        if alerts:
            print(f"\n  🚨 Alerts ({len(alerts)})")
            print(f"  {'─' * 70}")
            for alert in alerts:
                level_icon = {"critical": "🔴", "warning": "🟡"}.get(alert["level"], "⚪")
                print(f"    {level_icon} [{alert['level'].upper():8s}] {alert['source']:20s}: {alert['message']}")
        else:
            print(f"\n  ✅ No active alerts")

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Cross-Region Monitoring Dashboard")
    parser.add_argument("--watch", action="store_true",
                        help="Continuously monitor")
    parser.add_argument("--interval", type=int, default=30,
                        help="Refresh interval in seconds (default: 30)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    dashboard = CrossRegionDashboard()

    if args.watch:
        print("Monitoring HarchOS cross-region dashboard (Ctrl+C to stop)...")
        try:
            while True:
                data = dashboard.fetch_all_data()
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print("\033[2J\033[H", end="")
                    dashboard.render_dashboard(data)
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"\n  Last updated: {ts} | Next refresh in {args.interval}s")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped monitoring.")
    else:
        print("=" * 70)
        print("HarchOS Cross-Region Monitoring Dashboard")
        print("=" * 70)

        data = dashboard.fetch_all_data()

        if args.json:
            print(json.dumps(data, indent=2))
        else:
            dashboard.render_dashboard(data)
            print()


if __name__ == "__main__":
    main()
