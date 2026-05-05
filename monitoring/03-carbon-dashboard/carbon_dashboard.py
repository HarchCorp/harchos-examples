#!/usr/bin/env python3
"""Carbon metrics dashboard for HarchOS.

Builds a comprehensive carbon metrics dashboard using data from
the HarchOS SDK. Combines platform metrics, carbon intensity data,
and carbon-aware scheduling results into a unified view.

Features:
- Platform-wide carbon intensity monitoring
- Per-hub carbon breakdown
- CO2 savings from carbon-aware scheduling
- Green window detection and recommendations
- Carbon budget tracking
- Sovereignty-aware carbon reporting

Usage:
    python carbon_dashboard.py
    python carbon_dashboard.py --detailed
    python carbon_dashboard.py --carbon-budget 5000
    HARCHOS_API_KEY=hsk_... python carbon_dashboard.py
"""

import argparse
import json
import math
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOSClient
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated carbon data")


# ---------------------------------------------------------------------------
# Simulated carbon data
# ---------------------------------------------------------------------------

SIMULATED_HUBS = [
    {"name": "Harch Ouarzazate", "region": "morocco", "gpus": 800,
     "renewable_pct": 97.2, "carbon_intensity": 18, "active_workloads": 45},
    {"name": "Harch Dakhla", "region": "morocco", "gpus": 400,
     "renewable_pct": 94.8, "carbon_intensity": 32, "active_workloads": 22},
    {"name": "Harch Benguerir", "region": "morocco", "gpus": 350,
     "renewable_pct": 88.5, "carbon_intensity": 55, "active_workloads": 18},
    {"name": "Harch Tanger", "region": "morocco", "gpus": 200,
     "renewable_pct": 82.1, "carbon_intensity": 95, "active_workloads": 8},
    {"name": "Harch Casablanca", "region": "morocco", "gpus": 48,
     "renewable_pct": 45.0, "carbon_intensity": 210, "active_workloads": 3},
]

SIMULATED_PLATFORM_METRICS = {
    "total_hubs": 5,
    "total_gpus": 1798,
    "available_gpus": 423,
    "gpu_utilization_percent": 76.5,
    "total_workloads": 1247,
    "active_workloads": 96,
    "total_energy_kwh": 345678.5,
    "avg_renewable_percentage": 81.52,
    "avg_carbon_intensity": 47.0,
    "avg_pue": 1.12,
    "total_co2_saved_kg": 12456.3,
}


# ---------------------------------------------------------------------------
# Carbon Dashboard
# ---------------------------------------------------------------------------

class CarbonDashboard:
    """Builds and displays a carbon metrics dashboard for HarchOS."""

    # Thresholds for carbon intensity color coding
    GREEN_THRESHOLD = 100   # gCO2/kWh
    YELLOW_THRESHOLD = 200  # gCO2/kWh

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOSClient(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = None

    def fetch_dashboard_data(self) -> dict:
        """Fetch all data needed for the dashboard."""
        data = {
            "hubs": SIMULATED_HUBS,
            "platform_metrics": SIMULATED_PLATFORM_METRICS,
            "carbon_savings": self._compute_carbon_savings(),
            "green_windows": self._detect_green_windows(),
        }

        if self.client:
            try:
                # Try to get real carbon dashboard data
                carbon_dashboard = self.client.carbon.get_dashboard()
                data["carbon_dashboard"] = {
                    "metrics": {
                        "total_optimizations": getattr(carbon_dashboard, 'metrics', None),
                    }
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
                    "total_workloads": metrics.total_workloads,
                    "active_workloads": metrics.active_workloads,
                    "total_energy_kwh": metrics.total_energy_kwh,
                    "avg_renewable_percentage": metrics.avg_renewable_percentage,
                    "avg_carbon_intensity": metrics.avg_carbon_intensity,
                    "avg_pue": metrics.avg_pue,
                    "total_co2_saved_kg": metrics.total_co2_saved_kg,
                }
            except Exception:
                pass

        return data

    def _compute_carbon_savings(self) -> dict:
        """Compute carbon savings from using green hubs vs industry average."""
        # Industry average carbon intensity for data centers: ~450 gCO2/kWh
        INDUSTRY_AVG = 450.0
        harchos_avg = SIMULATED_PLATFORM_METRICS["avg_carbon_intensity"]
        total_energy = SIMULATED_PLATFORM_METRICS["total_energy_kwh"]

        # CO2 at industry average
        co2_industry = total_energy * INDUSTRY_AVG / 1000  # kg
        # CO2 at HarchOS average
        co2_harchos = total_energy * harchos_avg / 1000  # kg
        # Savings
        co2_saved = co2_industry - co2_harchos
        savings_pct = (1 - harchos_avg / INDUSTRY_AVG) * 100

        return {
            "co2_industry_kg": round(co2_industry, 1),
            "co2_harchos_kg": round(co2_harchos, 1),
            "co2_saved_kg": round(co2_saved, 1),
            "co2_saved_tonnes": round(co2_saved / 1000, 2),
            "savings_percentage": round(savings_pct, 1),
            "industry_avg_intensity": INDUSTRY_AVG,
            "harchos_avg_intensity": harchos_avg,
        }

    def _detect_green_windows(self) -> List[dict]:
        """Detect current green windows (hubs with low carbon intensity)."""
        windows = []
        for hub in SIMULATED_HUBS:
            if hub["carbon_intensity"] <= self.GREEN_THRESHOLD:
                windows.append({
                    "hub": hub["name"],
                    "carbon_intensity": hub["carbon_intensity"],
                    "renewable_pct": hub["renewable_pct"],
                    "available_gpus": hub["gpus"] - hub["active_workloads"] * 8,
                    "status": "optimal" if hub["carbon_intensity"] <= 50 else "green",
                })
        return windows

    def _carbon_icon(self, intensity: float) -> str:
        """Get color icon for carbon intensity level."""
        if intensity <= self.GREEN_THRESHOLD:
            return "🟢"
        elif intensity <= self.YELLOW_THRESHOLD:
            return "🟡"
        else:
            return "🔴"

    def render_dashboard(self, data: dict, detailed: bool = False):
        """Render the carbon dashboard."""
        print("\n  ╔════════════════════════════════════════════════════════════════╗")
        print("  ║          HarchOS Carbon Metrics Dashboard                     ║")
        print("  ╚════════════════════════════════════════════════════════════════╝")

        metrics = data["platform_metrics"]
        savings = data["carbon_savings"]
        hubs = data["hubs"]
        windows = data["green_windows"]

        # ── Overview ──────────────────────────────────────────────────────
        print(f"\n  🌍 Carbon Overview")
        print(f"  {'─' * 60}")
        print(f"    Average Carbon Intensity: {metrics['avg_carbon_intensity']:>6.1f} gCO2/kWh "
              f"{self._carbon_icon(metrics['avg_carbon_intensity'])}")
        print(f"    Average Renewable Share:  {metrics['avg_renewable_percentage']:>6.1f}%")
        print(f"    Total Energy Consumed:    {metrics['total_energy_kwh']:>10,.1f} kWh")
        print(f"    Average PUE:              {metrics['avg_pue']:>6.2f}")

        # ── Carbon Savings ───────────────────────────────────────────────
        print(f"\n  💚 Carbon Savings (vs Industry Average)")
        print(f"  {'─' * 60}")
        print(f"    Industry Average:     {savings['industry_avg_intensity']:>6.0f} gCO2/kWh")
        print(f"    HarchOS Average:      {savings['harchos_avg_intensity']:>6.0f} gCO2/kWh")
        print(f"    Savings:              {savings['savings_percentage']:>5.1f}%")
        print(f"    CO2 Avoided:          {savings['co2_saved_kg']:>10,.1f} kg "
              f"({savings['co2_saved_tonnes']:>6.2f} tonnes)")
        print(f"    CO2 Saved (Scheduled):{metrics['total_co2_saved_kg']:>10,.1f} kg")

        # ── Hub Breakdown ────────────────────────────────────────────────
        print(f"\n  🏭 Hub Carbon Breakdown")
        print(f"  {'─' * 60}")
        print(f"    {'Hub':22s} | {'gCO2/kWh':>8s} | {'Renewable':>9s} | {'GPUs':>5s} | Status")
        print(f"    {'─' * 22}-+-{'─' * 8}-+-{'─' * 9}-+-{'─' * 5}-+-{'─' * 10}")

        for hub in sorted(hubs, key=lambda h: h["carbon_intensity"]):
            icon = self._carbon_icon(hub["carbon_intensity"])
            status = "OPTIMAL" if hub["carbon_intensity"] <= 50 else (
                "GREEN" if hub["carbon_intensity"] <= self.GREEN_THRESHOLD else (
                    "ACCEPTABLE" if hub["carbon_intensity"] <= self.YELLOW_THRESHOLD else "AVOID"
                )
            )
            print(f"    {hub['name']:22s} | {hub['carbon_intensity']:>7.0f}  | "
                  f"{hub['renewable_pct']:>8.1f}% | {hub['gpus']:>5d} | {icon} {status}")

        # ── Green Windows ────────────────────────────────────────────────
        if windows:
            print(f"\n  🌿 Current Green Windows")
            print(f"  {'─' * 60}")
            for w in windows:
                print(f"    {self._carbon_icon(w['carbon_intensity'])} {w['hub']:22s} — "
                      f"{w['carbon_intensity']:.0f} gCO2/kWh | "
                      f"{w['renewable_pct']:.1f}% renewable | "
                      f"~{w['available_gpus']} GPUs available | {w['status'].upper()}")

        # ── Detailed View ────────────────────────────────────────────────
        if detailed:
            print(f"\n  📈 Detailed Carbon Analysis")
            print(f"  {'─' * 60}")

            # Per-hub energy estimate
            total_energy = metrics["total_energy_kwh"]
            total_gpus = metrics["total_gpus"]
            for hub in hubs:
                gpu_share = hub["gpus"] / total_gpus
                hub_energy = total_energy * gpu_share
                hub_co2 = hub_energy * hub["carbon_intensity"] / 1000  # kg
                hub_renewable_energy = hub_energy * hub["renewable_pct"] / 100

                print(f"\n    {hub['name']}:")
                print(f"      Estimated Energy:     {hub_energy:>10,.1f} kWh")
                print(f"      Estimated CO2:        {hub_co2:>10,.1f} kg")
                print(f"      Renewable Energy:     {hub_renewable_energy:>10,.1f} kWh")

            # Carbon budget equivalent
            print(f"\n    Carbon Equivalents:")
            co2_saved = savings["co2_saved_kg"]
            # Trees absorb ~22 kg CO2/year
            trees_equiv = co2_saved / 22
            # Average car emits ~4600 kg CO2/year
            cars_equiv = co2_saved / 4600
            print(f"      CO2 saved = {trees_equiv:,.0f} trees absorbing for 1 year")
            print(f"      CO2 saved = {cars_equiv:,.1f} cars off the road for 1 year")

    def check_carbon_budget(self, data: dict, budget_kg: float):
        """Check if carbon emissions are within budget."""
        metrics = data["platform_metrics"]
        savings = data["carbon_savings"]

        current_emissions = savings["co2_harchos_kg"]
        within_budget = current_emissions <= budget_kg

        print(f"\n  💰 Carbon Budget Check")
        print(f"  {'─' * 60}")
        print(f"    Carbon Budget:    {budget_kg:>10,.1f} kg CO2")
        print(f"    Current Emissions:{current_emissions:>10,.1f} kg CO2")
        print(f"    Budget Used:      {current_emissions / budget_kg * 100:>9.1f}%")
        print(f"    Remaining:        {max(0, budget_kg - current_emissions):>10,.1f} kg CO2")

        if within_budget:
            print(f"    ✅ Within carbon budget")
        else:
            overage = current_emissions - budget_kg
            print(f"    ❌ Over carbon budget by {overage:,.1f} kg CO2")
            print(f"    💡 Consider scheduling workloads during green windows")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Carbon Dashboard")
    parser.add_argument("--detailed", action="store_true",
                        help="Show detailed carbon analysis")
    parser.add_argument("--carbon-budget", type=float, default=None,
                        help="Carbon budget in kg CO2 (optional)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")
    args = parser.parse_args()

    dashboard = CarbonDashboard()

    print("=" * 60)
    print("HarchOS Carbon Dashboard")
    print("=" * 60)

    data = dashboard.fetch_dashboard_data()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        dashboard.render_dashboard(data, detailed=args.detailed)

        if args.carbon_budget is not None:
            dashboard.check_carbon_budget(data, args.carbon_budget)

        print()


if __name__ == "__main__":
    main()
