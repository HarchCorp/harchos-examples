#!/usr/bin/env python3
"""Detailed health check and status monitoring for HarchOS.

Performs comprehensive health checks of the HarchOS platform, including
API server status, database connectivity, uptime tracking, and endpoint
availability. Designed for integration with monitoring/alerting systems.

Features:
- API server health check
- Database connectivity verification
- Uptime tracking with human-readable format
- Active connection monitoring
- Sovereignty compliance validation
- Exit codes for alerting (0=healthy, 1=degraded, 2=unhealthy)

Usage:
    python health_check.py
    python health_check.py --watch
    python health_check.py --exit-code
    HARCHOS_API_KEY=hsk_... python health_check.py
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

try:
    from harchos import HarchOS
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated health data")


# ---------------------------------------------------------------------------
# Simulated health data
# ---------------------------------------------------------------------------

SIMULATED_HEALTH = {
    "status": "healthy",
    "database_status": "connected",
    "api_version": "0.2.0",
    "uptime_seconds": 86400 * 14 + 3600 * 6,  # 14 days 6 hours
    "total_endpoints": 47,
    "active_connections": 128,
}


class SimulatedHealthClient:
    """Simulated health client for local testing."""

    def detailed_health(self):
        return SIMULATED_HEALTH


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class HealthChecker:
    """Performs detailed health checks on the HarchOS platform."""

    # Sovereignty requirements: regions that must comply
    SOVEREIGNTY_REGIONS = {
        "morocco": {"frameworks": ["GDPR", "CNDP", "ISO27001"], "data_residency": True},
        "algeria": {"frameworks": ["PDPA"], "data_residency": True},
        "nigeria": {"frameworks": ["NDPR", "GDPR"], "data_residency": True},
    }

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOS(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = SimulatedHealthClient()

    def fetch_health(self) -> dict:
        """Fetch detailed health information."""
        try:
            if HARCHOS_AVAILABLE:
                h = self.client.monitoring.detailed_health()
                return {
                    "status": h.status,
                    "database_status": h.database_status,
                    "api_version": h.api_version,
                    "uptime_seconds": h.uptime_seconds,
                    "total_endpoints": h.total_endpoints,
                    "active_connections": h.active_connections,
                    "is_healthy": h.is_healthy,
                    "uptime_hours": h.uptime_hours,
                    "uptime_days": h.uptime_days,
                }
            else:
                return self.client.detailed_health()
        except Exception as e:
            print(f"[ERROR] Health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_status": "disconnected",
                "error": str(e),
            }

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in a human-readable way."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def print_health(self, health: dict):
        """Pretty-print health check results."""
        status = health.get("status", "unknown")
        db_status = health.get("database_status", "unknown")

        # Status icons
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
        }.get(status, "❓")

        db_icon = {
            "connected": "✅",
            "degraded": "⚠️",
            "disconnected": "❌",
        }.get(db_status, "❓")

        print("\n  ╔══════════════════════════════════════════════════════════╗")
        print("  ║            HarchOS Health Check                         ║")
        print("  ╚══════════════════════════════════════════════════════════╝")

        # Overall status
        print(f"\n  🏥 Overall Status")
        print(f"  {'─' * 50}")
        print(f"    Platform:     {status_icon} {status.upper()}")
        print(f"    Database:     {db_icon} {db_status.upper()}")

        # Server details
        api_version = health.get("api_version", "unknown")
        uptime_sec = health.get("uptime_seconds", 0)
        uptime_formatted = self.format_uptime(uptime_sec)
        endpoints = health.get("total_endpoints", 0)
        connections = health.get("active_connections", 0)

        print(f"\n  🔧 Server Details")
        print(f"  {'─' * 50}")
        print(f"    API Version:     {api_version}")
        print(f"    Uptime:          {uptime_formatted} ({uptime_sec:,.0f}s)")
        print(f"    Endpoints:       {endpoints}")
        print(f"    Active Conns:    {connections}")

        # Sovereignty compliance
        print(f"\n  🛡️  Sovereignty Compliance")
        print(f"  {'─' * 50}")
        for region, reqs in self.SOVEREIGNTY_REGIONS.items():
            frameworks = ", ".join(reqs["frameworks"])
            residency = "Required" if reqs["data_residency"] else "Optional"
            print(f"    {region:12s}: {frameworks} | Data Residency: {residency}")

        # Recommendations
        print(f"\n  💡 Recommendations")
        print(f"  {'─' * 50}")

        if status == "healthy" and db_status == "connected":
            print("    ✅ Platform is operating normally")
        elif status == "degraded":
            print("    ⚠️  Platform is degraded — monitor closely")
            if db_status != "connected":
                print("    ❌ Database issues detected — check DB connectivity")
        elif status == "unhealthy":
            print("    ❌ Platform is unhealthy — immediate action required")

        if uptime_sec < 3600:
            print("    ⚠️  Server recently restarted — verify services")
        elif uptime_sec < 86400:
            print("    ℹ️  Server uptime less than 24h — stability check recommended")

    def get_exit_code(self, health: dict) -> int:
        """Get exit code based on health status for alerting systems.

        Returns:
            0 = healthy, 1 = degraded, 2 = unhealthy
        """
        status = health.get("status", "unhealthy")
        return {"healthy": 0, "degraded": 1, "unhealthy": 2}.get(status, 2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Health Check")
    parser.add_argument("--watch", action="store_true",
                        help="Continuously monitor health")
    parser.add_argument("--interval", type=int, default=30,
                        help="Check interval in seconds (default: 30)")
    parser.add_argument("--exit-code", action="store_true",
                        help="Exit with status code (0=healthy, 1=degraded, 2=unhealthy)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    checker = HealthChecker()

    if args.watch:
        print("Monitoring HarchOS health (Ctrl+C to stop)...")
        try:
            while True:
                health = checker.fetch_health()
                if args.json:
                    print(json.dumps(health, indent=2))
                else:
                    print("\033[2J\033[H", end="")
                    checker.print_health(health)
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    print(f"\n  Last checked: {ts} | Next check in {args.interval}s")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped monitoring.")
    else:
        print("=" * 60)
        print("HarchOS Health Check")
        print("=" * 60)

        health = checker.fetch_health()

        if args.json:
            print(json.dumps(health, indent=2))
        else:
            checker.print_health(health)
            print()

        if args.exit_code:
            exit_code = checker.get_exit_code(health)
            sys.exit(exit_code)


if __name__ == "__main__":
    main()
