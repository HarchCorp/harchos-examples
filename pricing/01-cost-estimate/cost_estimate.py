#!/usr/bin/env python3
"""Cost estimation for HarchOS GPU workloads.

Calculates cost estimates for different GPU types, regions, and tiers
using the HarchOS Python SDK. Demonstrates how to plan spending before
deploying workloads — a key best practice for managing GPU budgets.

Features:
- Per-GPU, per-region cost estimation
- Multi-tier comparison (community, enterprise, sovereign)
- Carbon-cost trade-off analysis
- Budget validation before deployment

Usage:
    python cost_estimate.py
    python cost_estimate.py --gpu-type H100 --gpu-count 8 --hours 168
    HARCHOS_API_KEY=hsk_... python cost_estimate.py
"""

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOSClient
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated pricing data")


# ---------------------------------------------------------------------------
# Simulated pricing data (for local testing without a live HarchOS server)
# ---------------------------------------------------------------------------

SIMULATED_PLANS = [
    {
        "id": "plan-h100-ouarzazate",
        "name": "H100 Enterprise (Ouarzazate)",
        "gpu_type": "H100",
        "price_per_gpu_hour": 2.10,
        "price_per_cpu_core_hour": 0.04,
        "price_per_gb_storage_month": 0.08,
        "price_per_gb_memory_hour": 0.005,
        "currency": "USD",
        "region": "morocco",
        "tier": "enterprise",
        "is_default": True,
    },
    {
        "id": "plan-h100-ouarzazate-mad",
        "name": "H100 Enterprise (Ouarzazate, MAD)",
        "gpu_type": "H100",
        "price_per_gpu_hour": 21.00,
        "price_per_cpu_core_hour": 0.40,
        "price_per_gb_storage_month": 0.80,
        "price_per_gb_memory_hour": 0.05,
        "currency": "MAD",
        "region": "morocco",
        "tier": "enterprise",
        "is_default": False,
    },
    {
        "id": "plan-a100-tanger",
        "name": "A100 Performance (Tanger)",
        "gpu_type": "A100",
        "price_per_gpu_hour": 1.80,
        "price_per_cpu_core_hour": 0.035,
        "price_per_gb_storage_month": 0.07,
        "price_per_gb_memory_hour": 0.004,
        "currency": "USD",
        "region": "morocco",
        "tier": "enterprise",
        "is_default": False,
    },
    {
        "id": "plan-l40s-dakhla",
        "name": "L40S Enterprise (Dakhla)",
        "gpu_type": "L40S",
        "price_per_gpu_hour": 1.40,
        "price_per_cpu_core_hour": 0.03,
        "price_per_gb_storage_month": 0.06,
        "price_per_gb_memory_hour": 0.003,
        "currency": "USD",
        "region": "morocco",
        "tier": "enterprise",
        "is_default": False,
    },
    {
        "id": "plan-a100-casablanca",
        "name": "A100 Standard (Casablanca)",
        "gpu_type": "A100",
        "price_per_gpu_hour": 1.95,
        "price_per_cpu_core_hour": 0.038,
        "price_per_gb_storage_month": 0.075,
        "price_per_gb_memory_hour": 0.0045,
        "currency": "USD",
        "region": "morocco",
        "tier": "community",
        "is_default": False,
    },
]


class SimulatedPricingClient:
    """Simulated pricing client for local testing."""

    def estimate_cost(self, *, gpu_count, gpu_type, hours, region=None, tier=None):
        """Compute a cost estimate from simulated plan data."""
        # Find best matching plan
        matching = [p for p in SIMULATED_PLANS if p["gpu_type"] == gpu_type]
        if region:
            matching = [p for p in matching if p["region"] == region]
        if tier:
            matching = [p for p in matching if p["tier"] == tier]
        if not matching:
            # Fallback: use first plan
            matching = SIMULATED_PLANS[:1]

        plan = matching[0]
        gpu_cost = plan["price_per_gpu_hour"] * gpu_count * hours
        subtotal = gpu_cost
        discount = 0.0
        # Enterprise tier gets 5% discount for large workloads
        if plan["tier"] == "enterprise" and gpu_count >= 8:
            discount = 5.0
            subtotal = gpu_cost * (1 - discount / 100)

        return {
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "hours": hours,
            "region": region or plan["region"],
            "tier": tier or plan["tier"],
            "estimated_total": round(subtotal, 2),
            "currency": plan["currency"],
            "breakdown": {
                "gpu_cost": round(gpu_cost, 2),
                "cpu_cost": 0.0,
                "memory_cost": 0.0,
                "storage_cost": 0.0,
                "network_cost": 0.0,
                "discount_percentage": discount,
                "subtotal": round(subtotal, 2),
                "tax": round(subtotal * 0.2, 2),  # 20% VAT (Morocco)
            },
        }

    def list_plans(self, **filters):
        """Return simulated plans."""
        return SIMULATED_PLANS


# ---------------------------------------------------------------------------
# Cost Estimator
# ---------------------------------------------------------------------------

class CostEstimator:
    """Estimates and compares GPU deployment costs across HarchOS."""

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOSClient(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = SimulatedPricingClient()

    def estimate_single(
        self,
        gpu_count: int,
        gpu_type: str,
        hours: float,
        region: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> dict:
        """Estimate cost for a single workload configuration."""
        try:
            if HARCHOS_AVAILABLE:
                estimate = self.client.pricing.estimate_cost(
                    gpu_count=gpu_count,
                    gpu_type=gpu_type,
                    hours=hours,
                    region=region,
                    tier=tier,
                )
                return {
                    "gpu_count": estimate.gpu_count,
                    "gpu_type": estimate.gpu_type,
                    "hours": estimate.hours,
                    "region": estimate.region,
                    "tier": estimate.tier,
                    "estimated_total": estimate.estimated_total,
                    "currency": estimate.currency,
                    "breakdown": {
                        "gpu_cost": estimate.breakdown.gpu_cost,
                        "cpu_cost": estimate.breakdown.cpu_cost,
                        "memory_cost": estimate.breakdown.memory_cost,
                        "storage_cost": estimate.breakdown.storage_cost,
                        "network_cost": estimate.breakdown.network_cost,
                        "discount_percentage": estimate.breakdown.discount_percentage,
                        "subtotal": estimate.breakdown.subtotal,
                        "tax": estimate.breakdown.tax,
                    },
                }
            else:
                return self.client.estimate_cost(
                    gpu_count=gpu_count,
                    gpu_type=gpu_type,
                    hours=hours,
                    region=region,
                    tier=tier,
                )
        except Exception as e:
            print(f"[ERROR] Cost estimation failed: {e}")
            return {"error": str(e)}

    def estimate_multi_config(
        self,
        configs: List[Dict],
    ) -> List[dict]:
        """Estimate costs for multiple workload configurations."""
        results = []
        for cfg in configs:
            result = self.estimate_single(**cfg)
            result["_config"] = cfg
            results.append(result)
        return results

    def print_estimate(self, estimate: dict):
        """Pretty-print a cost estimate."""
        if "error" in estimate:
            print(f"  ❌ Error: {estimate['error']}")
            return

        print(f"\n  GPU:       {estimate['gpu_count']}x {estimate['gpu_type']}")
        print(f"  Hours:     {estimate['hours']}")
        print(f"  Region:    {estimate['region']}")
        print(f"  Tier:      {estimate['tier']}")
        print(f"  Currency:  {estimate['currency']}")
        print()
        bd = estimate["breakdown"]
        print(f"  ┌──────────────────────────────────────────────┐")
        print(f"  │ GPU Compute:      {bd['gpu_cost']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  │ CPU Compute:      {bd['cpu_cost']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  │ Memory:           {bd['memory_cost']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  │ Storage:          {bd['storage_cost']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  │ Network:          {bd['network_cost']:>10.2f} {estimate['currency']:>3s}           │")
        if bd["discount_percentage"] > 0:
            print(f"  │ Discount:         {bd['discount_percentage']:>9.1f}%              │")
        print(f"  │ Subtotal:         {bd['subtotal']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  │ Tax (VAT):        {bd['tax']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  ├──────────────────────────────────────────────┤")
        print(f"  │ ESTIMATED TOTAL:  {estimate['estimated_total']:>10.2f} {estimate['currency']:>3s}           │")
        print(f"  └──────────────────────────────────────────────┘")

    def validate_budget(
        self,
        estimate: dict,
        budget: float,
        currency: str = "USD",
    ) -> bool:
        """Check whether an estimate fits within a given budget."""
        if "error" in estimate:
            return False
        if estimate["currency"] != currency:
            print(f"  ⚠️  Currency mismatch: estimate is {estimate['currency']}, budget is {currency}")
            # Simple MAD → USD conversion for demo
            if estimate["currency"] == "MAD" and currency == "USD":
                converted = estimate["estimated_total"] / 10.0
                return converted <= budget
            if estimate["currency"] == "USD" and currency == "MAD":
                converted = estimate["estimated_total"] * 10.0
                return converted <= budget
        return estimate["estimated_total"] <= budget


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Cost Estimator")
    parser.add_argument("--gpu-type", type=str, default="H100",
                        help="GPU type (H100, A100, L40S)")
    parser.add_argument("--gpu-count", type=int, default=4,
                        help="Number of GPUs")
    parser.add_argument("--hours", type=float, default=24.0,
                        help="Usage duration in hours")
    parser.add_argument("--region", type=str, default="morocco",
                        help="Target region")
    parser.add_argument("--tier", type=str, default=None,
                        help="Pricing tier (community, enterprise, sovereign)")
    parser.add_argument("--budget", type=float, default=None,
                        help="Budget limit in USD (optional)")
    parser.add_argument("--compare", action="store_true",
                        help="Compare across all GPU types")
    args = parser.parse_args()

    estimator = CostEstimator()

    print("=" * 60)
    print("HarchOS Cost Estimator")
    print("=" * 60)

    if args.compare:
        # Compare across all GPU types
        print("\n📊 Comparing costs across GPU types...")
        print(f"   Configuration: {args.gpu_count} GPUs, {args.hours}h, {args.region}")

        gpu_types = ["H100", "A100", "L40S"]
        configs = [
            {"gpu_count": args.gpu_count, "gpu_type": gt, "hours": args.hours,
             "region": args.region, "tier": args.tier}
            for gt in gpu_types
        ]

        results = estimator.estimate_multi_config(configs)
        for result in results:
            if "error" not in result:
                gpu_type = result["gpu_type"]
                total = result["estimated_total"]
                currency = result["currency"]
                per_gpu_hr = result["breakdown"]["gpu_cost"] / max(result["gpu_count"] * result["hours"], 1)
                print(f"   {gpu_type:6s}: {total:>10.2f} {currency} total "
                      f"({per_gpu_hr:.2f} {currency}/gpu/hr)")
                estimator.print_estimate(result)
    else:
        # Single estimate
        print(f"\n💰 Estimating cost for {args.gpu_count}x {args.gpu_type} "
              f"for {args.hours}h in {args.region}...")
        estimate = estimator.estimate_single(
            gpu_count=args.gpu_count,
            gpu_type=args.gpu_type,
            hours=args.hours,
            region=args.region,
            tier=args.tier,
        )
        estimator.print_estimate(estimate)

        # Budget check
        if args.budget is not None:
            within_budget = estimator.validate_budget(estimate, args.budget)
            if within_budget:
                print(f"\n  ✅ Within budget (${args.budget:.2f} USD)")
            else:
                print(f"\n  ❌ Exceeds budget (${args.budget:.2f} USD)")
                print(f"     Consider using a different GPU type or fewer GPUs")


if __name__ == "__main__":
    main()
