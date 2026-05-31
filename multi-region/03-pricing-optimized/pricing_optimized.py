#!/usr/bin/env python3
"""Pricing-optimized multi-region deployment for HarchOS.

Deploys workloads across HarchOS regions optimized for cost while
respecting carbon intensity thresholds and sovereignty requirements.
Combines the pricing and regions APIs to find the best-value hub
for each workload.

Features:
- Cross-region cost comparison before deployment
- Carbon-intensity constraints on hub selection
- Sovereignty enforcement (data residency compliance)
- Tier-aware pricing optimization
- Deployment recommendation engine

Usage:
    python pricing_optimized.py --gpu-type H100 --gpu-count 8 --hours 168
    python pricing_optimized.py --carbon-max 100 --tier enterprise
    python pricing_optimized.py --sovereign-only
    HARCHOS_API_KEY=hsk_... python pricing_optimized.py
"""

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOS
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated data")


# ---------------------------------------------------------------------------
# Simulated data
# ---------------------------------------------------------------------------

SIMULATED_REGIONS = [
    {
        "name": "Morocco", "code": "morocco", "country": "MA",
        "available": True, "hub_count": 5, "total_gpus": 1798,
        "avg_renewable_percentage": 81.52, "avg_carbon_intensity": 47.0,
        "latency_ms_from_casablanca": 0,
        "compliance_frameworks": ["GDPR", "CNDP", "ISO27001"],
    },
    {
        "name": "Nigeria", "code": "nigeria", "country": "NG",
        "available": False, "hub_count": 0, "total_gpus": 0,
        "avg_renewable_percentage": 0, "avg_carbon_intensity": 0,
        "latency_ms_from_casablanca": 85,
        "compliance_frameworks": ["NDPR", "GDPR"],
    },
    {
        "name": "Kenya", "code": "kenya", "country": "KE",
        "available": False, "hub_count": 0, "total_gpus": 0,
        "avg_renewable_percentage": 0, "avg_carbon_intensity": 0,
        "latency_ms_from_casablanca": 120,
        "compliance_frameworks": ["PDPA", "GDPR"],
    },
]

SIMULATED_HUBS = [
    {"name": "Harch Ouarzazate", "region": "morocco", "gpus": 800,
     "renewable_pct": 97.2, "carbon_intensity": 18,
     "gpu_type": "H100", "price_per_gpu_hour": 2.10, "tier": "enterprise"},
    {"name": "Harch Dakhla", "region": "morocco", "gpus": 400,
     "renewable_pct": 94.8, "carbon_intensity": 32,
     "gpu_type": "L40S", "price_per_gpu_hour": 1.40, "tier": "enterprise"},
    {"name": "Harch Benguerir", "region": "morocco", "gpus": 350,
     "renewable_pct": 88.5, "carbon_intensity": 55,
     "gpu_type": "H100", "price_per_gpu_hour": 2.35, "tier": "performance"},
    {"name": "Harch Tanger", "region": "morocco", "gpus": 200,
     "renewable_pct": 82.1, "carbon_intensity": 95,
     "gpu_type": "A100", "price_per_gpu_hour": 1.80, "tier": "enterprise"},
    {"name": "Harch Casablanca", "region": "morocco", "gpus": 48,
     "renewable_pct": 45.0, "carbon_intensity": 210,
     "gpu_type": "A100", "price_per_gpu_hour": 1.95, "tier": "community"},
]


# ---------------------------------------------------------------------------
# Pricing-Optimized Deployer
# ---------------------------------------------------------------------------

class PricingOptimizedDeployer:
    """Deploys workloads to the most cost-effective hub across regions."""

    # Required sovereignty frameworks per region
    SOVEREIGNTY_RULES = {
        "morocco": {"frameworks": ["GDPR", "CNDP"], "data_residency": True},
        "nigeria": {"frameworks": ["NDPR"], "data_residency": True},
        "kenya": {"frameworks": ["PDPA"], "data_residency": True},
    }

    def __init__(self, carbon_max: float = 200.0, tier: Optional[str] = None,
                 sovereign_only: bool = False):
        self.carbon_max = carbon_max
        self.tier = tier
        self.sovereign_only = sovereign_only

        if HARCHOS_AVAILABLE:
            self.client = HarchOS(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = None

    def get_regions(self) -> List[dict]:
        """Fetch available regions."""
        if self.client:
            try:
                regions = self.client.regions.list(available=True)
                return [
                    {
                        "name": r.name, "code": r.code, "country": r.country,
                        "available": r.available, "hub_count": r.hub_count,
                        "total_gpus": r.total_gpus,
                        "avg_renewable_percentage": r.avg_renewable_percentage,
                        "avg_carbon_intensity": r.avg_carbon_intensity,
                        "latency_ms_from_casablanca": r.latency_ms_from_casablanca or 0,
                        "compliance_frameworks": r.compliance_frameworks,
                    }
                    for r in regions
                ]
            except Exception:
                pass

        return [r for r in SIMULATED_REGIONS if r["available"]]

    def get_eligible_hubs(self, gpu_type: str, gpu_count: int) -> List[dict]:
        """Find hubs that match GPU type, count, carbon, and tier constraints."""
        eligible = []

        for hub in SIMULATED_HUBS:
            # GPU type check
            if hub["gpu_type"] != gpu_type:
                continue

            # GPU count check
            if hub["gpus"] < gpu_count:
                continue

            # Carbon check
            if hub["carbon_intensity"] > self.carbon_max:
                continue

            # Tier check
            if self.tier and hub["tier"] != self.tier:
                continue

            # Sovereignty check
            if self.sovereign_only:
                region_code = hub["region"]
                rules = self.SOVEREIGNTY_RULES.get(region_code, {})
                if not rules.get("data_residency", False):
                    continue

            eligible.append(hub)

        # Sort by price (ascending)
        eligible.sort(key=lambda h: h["price_per_gpu_hour"])
        return eligible

    def recommend_deployment(
        self,
        gpu_type: str,
        gpu_count: int,
        hours: float,
    ) -> dict:
        """Recommend the best hub for deployment based on price + carbon."""
        regions = self.get_regions()
        eligible_hubs = self.get_eligible_hubs(gpu_type, gpu_count)

        if not eligible_hubs:
            # Try relaxing constraints
            all_matching = [
                h for h in SIMULATED_HUBS
                if h["gpu_type"] == gpu_type and h["gpus"] >= gpu_count
            ]
            if all_matching:
                cheapest = min(all_matching, key=lambda h: h["price_per_gpu_hour"])
                return {
                    "recommendation": "relax_constraints",
                    "reason": f"No hubs within carbon limit ({self.carbon_max} gCO2/kWh)",
                    "cheapest_available": cheapest["name"],
                    "cheapest_carbon": cheapest["carbon_intensity"],
                    "suggestion": f"Increase --carbon-max to at least {cheapest['carbon_intensity']}",
                }
            return {
                "recommendation": "no_suitable_hub",
                "reason": f"No hubs with {gpu_count}x {gpu_type} GPUs available",
            }

        # Best option: cheapest eligible hub
        best = eligible_hubs[0]
        estimated_cost = best["price_per_gpu_hour"] * gpu_count * hours

        return {
            "recommendation": "deploy",
            "hub": best["name"],
            "region": best["region"],
            "gpu_type": best["gpu_type"],
            "gpu_count": gpu_count,
            "price_per_gpu_hour": best["price_per_gpu_hour"],
            "carbon_intensity": best["carbon_intensity"],
            "renewable_pct": best["renewable_pct"],
            "estimated_cost": round(estimated_cost, 2),
            "currency": "USD",
            "hours": hours,
            "tier": best["tier"],
            "alternatives": [
                {
                    "hub": h["name"],
                    "price_per_gpu_hour": h["price_per_gpu_hour"],
                    "carbon_intensity": h["carbon_intensity"],
                    "estimated_cost": round(h["price_per_gpu_hour"] * gpu_count * hours, 2),
                }
                for h in eligible_hubs[1:]
            ],
            "sovereignty": self.SOVEREIGNTY_RULES.get(best["region"], {}),
        }

    def print_recommendation(self, rec: dict):
        """Pretty-print the deployment recommendation."""
        if rec["recommendation"] == "no_suitable_hub":
            print(f"\n  ❌ {rec['reason']}")
            return

        if rec["recommendation"] == "relax_constraints":
            print(f"\n  ⚠️  {rec['reason']}")
            print(f"     Cheapest available: {rec['cheapest_available']} "
                  f"({rec['cheapest_carbon']} gCO2/kWh)")
            print(f"     Suggestion: {rec['suggestion']}")
            return

        print(f"\n  🎯 Deployment Recommendation")
        print(f"  {'─' * 60}")
        print(f"    Hub:               {rec['hub']}")
        print(f"    Region:            {rec['region']}")
        print(f"    GPU:               {rec['gpu_count']}x {rec['gpu_type']}")
        print(f"    Tier:              {rec['tier']}")
        print(f"    Duration:          {rec['hours']} hours")
        print(f"    Price/GPU/hr:      ${rec['price_per_gpu_hour']:.2f}")
        print(f"    Carbon Intensity:  {rec['carbon_intensity']} gCO2/kWh")
        print(f"    Renewable:         {rec['renewable_pct']:.1f}%")
        print(f"    Estimated Cost:    ${rec['estimated_cost']:.2f} {rec['currency']}")

        # Sovereignty info
        sovereignty = rec.get("sovereignty", {})
        if sovereignty:
            print(f"\n  🛡️  Sovereignty")
            print(f"    Data Residency:    {'Required ✅' if sovereignty.get('data_residency') else 'Optional'}")
            frameworks = sovereignty.get("frameworks", [])
            if frameworks:
                print(f"    Compliance:        {', '.join(frameworks)}")

        # Alternatives
        alternatives = rec.get("alternatives", [])
        if alternatives:
            print(f"\n  🔄 Alternatives (sorted by price)")
            print(f"  {'─' * 60}")
            for alt in alternatives:
                carbon_icon = "🟢" if alt["carbon_intensity"] <= 100 else (
                    "🟡" if alt["carbon_intensity"] <= 200 else "🔴")
                print(f"    {carbon_icon} {alt['hub']:25s} | "
                      f"${alt['price_per_gpu_hour']:.2f}/gpu/hr | "
                      f"{alt['carbon_intensity']} gCO2/kWh | "
                      f"${alt['estimated_cost']:.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pricing-Optimized Multi-Region Deployment")
    parser.add_argument("--gpu-type", type=str, default="H100",
                        help="GPU type (H100, A100, L40S)")
    parser.add_argument("--gpu-count", type=int, default=4,
                        help="Number of GPUs needed")
    parser.add_argument("--hours", type=float, default=24.0,
                        help="Estimated usage hours")
    parser.add_argument("--carbon-max", type=float, default=200.0,
                        help="Maximum carbon intensity in gCO2/kWh")
    parser.add_argument("--tier", type=str, default=None,
                        choices=["community", "enterprise", "sovereign"],
                        help="Required pricing tier")
    parser.add_argument("--sovereign-only", action="store_true",
                        help="Only consider sovereign-compliant hubs")
    args = parser.parse_args()

    deployer = PricingOptimizedDeployer(
        carbon_max=args.carbon_max,
        tier=args.tier,
        sovereign_only=args.sovereign_only,
    )

    print("=" * 60)
    print("HarchOS Pricing-Optimized Multi-Region Deployment")
    print("=" * 60)

    # Show available regions
    regions = deployer.get_regions()
    print(f"\n  📍 Available Regions: {len(regions)}")
    for r in regions:
        print(f"    • {r['name']} ({r['code']}): {r['hub_count']} hubs, "
              f"{r['total_gpus']} GPUs, {r['avg_renewable_percentage']:.1f}% renewable")

    # Get recommendation
    print(f"\n  🔍 Finding best hub for {args.gpu_count}x {args.gpu_type} "
          f"({args.hours}h, carbon ≤ {args.carbon_max} gCO2/kWh)...")

    rec = deployer.recommend_deployment(
        gpu_type=args.gpu_type,
        gpu_count=args.gpu_count,
        hours=args.hours,
    )
    deployer.print_recommendation(rec)
    print()


if __name__ == "__main__":
    main()
