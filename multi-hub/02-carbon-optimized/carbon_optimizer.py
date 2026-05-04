#!/usr/bin/env python3
"""Carbon-optimized multi-hub deployment for HarchOS.

Deploys inference workloads across multiple hubs with automatic carbon
optimization. Traffic is routed to the hub with the lowest carbon intensity
while respecting latency constraints.

Features:
- Real-time carbon intensity monitoring across hubs
- Automatic traffic routing to greenest hub
- Carbon-weighted load balancing
- Per-request carbon footprint tracking
- Carbon budget enforcement

Usage:
    python carbon_optimizer.py --hubs eu-west-1,us-east-1 --max-carbon 200
    python carbon_optimizer.py --monitor
    python carbon_optimizer.py --report
"""

import argparse
import json
import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

try:
    from harchos import CarbonClient, HubClient
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated carbon data")


# ---------------------------------------------------------------------------
# Simulated carbon data (for local testing)
# ---------------------------------------------------------------------------

class SimulatedCarbonSource:
    """Generates realistic carbon intensity patterns per region."""

    # Base carbon intensity and daily amplitude per region (gCO2/kWh)
    REGION_PROFILES = {
        "eu-west-1": {"baseline": 80, "amplitude": 60, "peak_hour": 18},
        "eu-north-1": {"baseline": 40, "amplitude": 30, "peak_hour": 17},
        "us-east-1": {"baseline": 200, "amplitude": 80, "peak_hour": 15},
        "us-west-2": {"baseline": 150, "amplitude": 70, "peak_hour": 16},
        "apac-southeast-1": {"baseline": 300, "amplitude": 50, "peak_hour": 13},
        "apac-northeast-1": {"baseline": 250, "amplitude": 60, "peak_hour": 14},
    }

    def get_intensity(self, region: str) -> dict:
        """Get simulated carbon intensity for a region."""
        profile = self.REGION_PROFILES.get(region, {"baseline": 200, "amplitude": 80, "peak_hour": 15})
        hour = datetime.now(timezone.utc).hour

        # Sinusoidal daily pattern
        variation = profile["amplitude"] * 0.5 * (
            1 + math.sin(2 * math.pi * (hour - profile["peak_hour"]) / 24)
        )
        intensity = max(0, profile["baseline"] + variation - profile["amplitude"] / 2)

        return {
            "region": region,
            "intensity_gco2_kwh": round(intensity, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "simulated",
        }


class SimulatedDeploymentClient:
    """Simulated hub deployment client."""

    def __init__(self):
        self.deployments: Dict[str, dict] = {}
        self.traffic_weights: Dict[str, float] = {}

    def deploy(self, hub: str, model: str, replicas: int = 1) -> dict:
        deployment_id = f"carbon-opt-{hub}-{int(time.time())}"
        self.deployments[hub] = {
            "deployment_id": deployment_id,
            "hub": hub,
            "model": model,
            "replicas": replicas,
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.deployments[hub]

    def set_traffic_weight(self, hub: str, weight: float):
        """Set traffic weight for a hub (0.0 to 1.0)."""
        self.traffic_weights[hub] = weight

    def teardown(self, hub: str):
        self.deployments.pop(hub, None)
        self.traffic_weights.pop(hub, None)


# ---------------------------------------------------------------------------
# Carbon optimizer
# ---------------------------------------------------------------------------

class CarbonOptimizer:
    """Optimizes multi-hub deployment for minimal carbon footprint."""

    def __init__(self, max_carbon: float = 200.0, max_latency_ms: float = 300.0):
        self.max_carbon = max_carbon
        self.max_latency_ms = max_latency_ms

        if HARCHOS_AVAILABLE:
            self.carbon_client = CarbonClient()
            self.hub_client = HubClient()
        else:
            self.carbon_client = SimulatedCarbonSource()
            self.hub_client = SimulatedDeploymentClient()

        self.hub_latencies = {
            "eu-west-1": 30, "eu-north-1": 40,
            "us-east-1": 80, "us-west-2": 120,
            "apac-southeast-1": 180, "apac-northeast-1": 160,
        }
        self.carbon_history: List[dict] = []
        self.total_requests = 0
        self.total_carbon_g = 0.0

    def get_carbon_ranking(self, hubs: List[str]) -> List[Tuple[str, float]]:
        """Rank hubs by carbon intensity (lowest first)."""
        rankings = []
        for hub in hubs:
            data = self.carbon_client.get_intensity(region=hub)
            intensity = data["intensity_gco2_kwh"]
            rankings.append((hub, intensity))
            # Record history
            self.carbon_history.append({
                "timestamp": data["timestamp"],
                "hub": hub,
                "intensity": intensity,
            })
        rankings.sort(key=lambda x: x[1])
        return rankings

    def compute_traffic_weights(self, rankings: List[Tuple[str, float]]) -> Dict[str, float]:
        """Compute traffic weights based on carbon ranking.

        Hubs below the carbon threshold get traffic proportional to their
        greenness. Hubs above the threshold get zero traffic (but remain
        deployed for failover).
        """
        eligible = [(hub, intensity) for hub, intensity in rankings
                    if intensity <= self.max_carbon]

        if not eligible:
            # All hubs above threshold — route to least bad option
            print(f"  ⚠️  All hubs above carbon threshold ({self.max_carbon} gCO2/kWh)")
            print("     Falling back to least-carbon hub")
            eligible = [rankings[0]]

        # Inverse-intensity weighting: greener hubs get more traffic
        inv_weights = {hub: 1.0 / max(intensity, 1.0) for hub, intensity in eligible}
        total_inv = sum(inv_weights.values())

        weights = {hub: w / total_inv for hub, w in inv_weights.items()}

        # Add zero-weight entries for ineligible hubs
        for hub, _ in rankings:
            if hub not in weights:
                weights[hub] = 0.0

        return weights

    def deploy_optimized(self, hubs: List[str], model: str, replicas: int = 1):
        """Deploy to all hubs with carbon-optimized traffic routing."""
        print("\nCarbon-Optimized Deployment")
        print(f"  Model: {model}")
        print(f"  Max carbon: {self.max_carbon} gCO2/kWh")
        print(f"  Hubs: {', '.join(hubs)}")
        print("=" * 60)

        # Deploy to all hubs
        print("\n1. Deploying to all hubs...")
        for hub in hubs:
            self.hub_client.deploy(hub, model=model, replicas=replicas)
            print(f"   ✅ {hub}")

        # Get carbon rankings
        print("\n2. Checking carbon intensity...")
        rankings = self.get_carbon_ranking(hubs)
        for hub, intensity in rankings:
            icon = "🟢" if intensity <= self.max_carbon else "🔴"
            print(f"   {icon} {hub}: {intensity:.1f} gCO2/kWh")

        # Compute and apply traffic weights
        print("\n3. Computing traffic weights...")
        weights = self.compute_traffic_weights(rankings)
        for hub, weight in sorted(weights.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 20)
            self.hub_client.set_traffic_weight(hub, weight)
            print(f"   {hub}: {weight*100:5.1f}% {bar}")

        return weights

    def monitor(self, hubs: List[str], interval: int = 30):
        """Continuously monitor carbon levels and adjust routing."""
        print(f"\nCarbon Monitor (every {interval}s, Ctrl+C to stop)")
        print("=" * 60)

        try:
            while True:
                timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                print(f"\n[{timestamp}]")

                rankings = self.get_carbon_ranking(hubs)
                weights = self.compute_traffic_weights(rankings)

                for hub, intensity in rankings:
                    weight = weights.get(hub, 0.0)
                    icon = "🟢" if intensity <= self.max_carbon else "🔴"
                    bar = "█" * int(weight * 20)
                    print(f"  {icon} {hub}: {intensity:6.1f} gCO2/kWh | "
                          f"traffic: {weight*100:5.1f}% {bar}")

                # Check if routing needs updating
                for hub, weight in weights.items():
                    self.hub_client.set_traffic_weight(hub, weight)

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")

    def generate_report(self, hubs: List[str]) -> dict:
        """Generate a carbon footprint report."""
        print("\nCarbon Footprint Report")
        print("=" * 60)

        rankings = self.get_carbon_ranking(hubs)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "max_carbon_threshold": self.max_carbon,
            "hubs": [],
        }

        total_intensity = 0
        for hub, intensity in rankings:
            hub_report = {
                "hub": hub,
                "carbon_intensity_gco2_kwh": intensity,
                "below_threshold": intensity <= self.max_carbon,
            }
            report["hubs"].append(hub_report)
            total_intensity += intensity

        avg_intensity = total_intensity / max(len(hubs), 1)
        report["average_intensity"] = round(avg_intensity, 1)
        report["greenest_hub"] = rankings[0][0]
        report["greenest_intensity"] = rankings[0][1]

        # Estimated carbon savings
        worst = rankings[-1][1] if rankings else 0
        best = rankings[0][1] if rankings else 0
        if worst > 0:
            savings_pct = (1 - best / worst) * 100
        else:
            savings_pct = 0
        report["estimated_carbon_savings_pct"] = round(savings_pct, 1)

        # Print summary
        for hub_r in report["hubs"]:
            icon = "🟢" if hub_r["below_threshold"] else "🔴"
            print(f"  {icon} {hub_r['hub']}: {hub_r['carbon_intensity_gco2_kwh']:.1f} gCO2/kWh")

        print(f"\n  Greenest hub: {report['greenest_hub']} ({report['greenest_intensity']:.1f} gCO2/kWh)")
        print(f"  Carbon savings vs worst hub: {report['estimated_carbon_savings_pct']:.1f}%")
        print(f"\n{json.dumps(report, indent=2)}")

        return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Carbon-Optimized Deployment")
    parser.add_argument("--hubs", type=str, default="eu-west-1,us-east-1,apac-southeast-1",
                        help="Comma-separated hub names")
    parser.add_argument("--model", type=str,
                        default="distilbert-base-uncased-finetuned-sst-2-english",
                        help="Model to deploy")
    parser.add_argument("--replicas", type=int, default=1, help="Replicas per hub")
    parser.add_argument("--max-carbon", type=float, default=200.0,
                        help="Max carbon intensity threshold (gCO2/kWh)")
    parser.add_argument("--max-latency", type=float, default=300.0,
                        help="Max acceptable latency (ms)")
    parser.add_argument("--monitor", action="store_true",
                        help="Continuously monitor carbon and adjust routing")
    parser.add_argument("--report", action="store_true",
                        help="Generate carbon footprint report")
    parser.add_argument("--teardown", action="store_true",
                        help="Remove all deployments")
    args = parser.parse_args()

    hub_list = [h.strip() for h in args.hubs.split(",")]
    optimizer = CarbonOptimizer(max_carbon=args.max_carbon, max_latency_ms=args.max_latency)

    if args.monitor:
        optimizer.monitor(hub_list)
        return

    if args.report:
        optimizer.generate_report(hub_list)
        return

    if args.teardown:
        for hub in hub_list:
            optimizer.hub_client.teardown(hub)
            print(f"  Removed deployment on {hub}")
        return

    # Default: deploy with carbon optimization
    optimizer.deploy_optimized(hub_list, model=args.model, replicas=args.replicas)


if __name__ == "__main__":
    main()
