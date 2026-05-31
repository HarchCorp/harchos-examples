#!/usr/bin/env python3
"""Price comparison across HarchOS regions and tiers.

Compares GPU pricing plans across different regions, tiers, and GPU types
to find the most cost-effective deployment configuration. Also factors in
carbon intensity for truly optimized decision-making.

Features:
- Cross-region price comparison
- Tier-based pricing analysis (community vs enterprise vs sovereign)
- Carbon-adjusted cost scoring
- Best-value recommendation engine

Usage:
    python price_comparison.py
    python price_comparison.py --gpu-type H100
    python price_comparison.py --include-carbon
    HARCHOS_API_KEY=hsk_... python price_comparison.py
"""

import argparse
import json
import os
from typing import Dict, List, Optional

try:
    from harchos import HarchOS
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated data")


# ---------------------------------------------------------------------------
# Simulated data (for local testing)
# ---------------------------------------------------------------------------

SIMULATED_PLANS = [
    {"id": "p1", "name": "H100 Enterprise (Ouarzazate)", "gpu_type": "H100",
     "price_per_gpu_hour": 2.10, "currency": "USD", "region": "morocco",
     "tier": "enterprise", "hub": "Ouarzazate", "carbon_intensity": 18,
     "renewable_pct": 97.2},
    {"id": "p2", "name": "H100 Enterprise (MAD)", "gpu_type": "H100",
     "price_per_gpu_hour": 21.00, "currency": "MAD", "region": "morocco",
     "tier": "enterprise", "hub": "Ouarzazate", "carbon_intensity": 18,
     "renewable_pct": 97.2},
    {"id": "p3", "name": "H100 Performance (Benguerir)", "gpu_type": "H100",
     "price_per_gpu_hour": 2.35, "currency": "USD", "region": "morocco",
     "tier": "enterprise", "hub": "Benguerir", "carbon_intensity": 55,
     "renewable_pct": 88.5},
    {"id": "p4", "name": "A100 Performance (Tanger)", "gpu_type": "A100",
     "price_per_gpu_hour": 1.80, "currency": "USD", "region": "morocco",
     "tier": "enterprise", "hub": "Tanger", "carbon_intensity": 95,
     "renewable_pct": 82.1},
    {"id": "p5", "name": "A100 Standard (Casablanca)", "gpu_type": "A100",
     "price_per_gpu_hour": 1.95, "currency": "USD", "region": "morocco",
     "tier": "community", "hub": "Casablanca", "carbon_intensity": 210,
     "renewable_pct": 45.0},
    {"id": "p6", "name": "L40S Enterprise (Dakhla)", "gpu_type": "L40S",
     "price_per_gpu_hour": 1.40, "currency": "USD", "region": "morocco",
     "tier": "enterprise", "hub": "Dakhla", "carbon_intensity": 32,
     "renewable_pct": 94.8},
    {"id": "p7", "name": "L40S Performance (Benguerir)", "gpu_type": "L40S",
     "price_per_gpu_hour": 1.55, "currency": "USD", "region": "morocco",
     "tier": "performance", "hub": "Benguerir", "carbon_intensity": 55,
     "renewable_pct": 88.5},
]


# ---------------------------------------------------------------------------
# Price Comparator
# ---------------------------------------------------------------------------

class PriceComparator:
    """Compares HarchOS pricing across regions, tiers, and GPU types."""

    # Carbon cost factor: higher carbon = higher effective cost
    # This represents the "hidden cost" of carbon (estimated $50/tonne CO2)
    CARBON_COST_PER_KG = 0.05  # USD per kg CO2

    def __init__(self):
        if HARCHOS_AVAILABLE:
            self.client = HarchOS(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        else:
            self.client = None
        self.plans = SIMULATED_PLANS

    def fetch_plans(self, gpu_type: Optional[str] = None, tier: Optional[str] = None):
        """Fetch pricing plans, optionally filtered."""
        if self.client:
            try:
                plans = self.client.pricing.list_plans(gpu_type=gpu_type, tier=tier)
                self.plans = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "gpu_type": p.gpu_type,
                        "price_per_gpu_hour": p.price_per_gpu_hour,
                        "currency": p.currency,
                        "region": p.region,
                        "tier": p.tier,
                    }
                    for p in plans
                ]
            except Exception as e:
                print(f"[WARN] SDK call failed: {e} — using simulated plans")

        # Apply filters to simulated plans too
        filtered = self.plans
        if gpu_type:
            filtered = [p for p in filtered if p["gpu_type"] == gpu_type]
        if tier:
            filtered = [p for p in filtered if p["tier"] == tier]
        return filtered

    def compare_prices(
        self,
        gpu_type: Optional[str] = None,
        tier: Optional[str] = None,
        hours: float = 730.0,
        gpu_count: int = 1,
        include_carbon: bool = False,
    ) -> List[dict]:
        """Compare prices across plans with optional carbon adjustment."""
        plans = self.fetch_plans(gpu_type=gpu_type, tier=tier)

        results = []
        for plan in plans:
            # Skip non-USD plans for fair comparison
            if plan["currency"] != "USD":
                continue

            monthly_cost = plan["price_per_gpu_hour"] * gpu_count * hours
            result = {
                **plan,
                "monthly_cost": round(monthly_cost, 2),
                "cost_per_gpu_hour": plan["price_per_gpu_hour"],
            }

            if include_carbon:
                carbon_intensity = plan.get("carbon_intensity", 100)
                # Estimated CO2 per GPU-hour: ~0.3 kWh * carbon_intensity / 1000
                co2_per_gpu_hr = 0.3 * carbon_intensity / 1000  # kg CO2
                carbon_cost_per_hr = co2_per_gpu_hr * self.CARBON_COST_PER_KG
                effective_cost_per_hr = plan["price_per_gpu_hour"] + carbon_cost_per_hr
                result["co2_per_gpu_hr_kg"] = round(co2_per_gpu_hr, 4)
                result["carbon_cost_per_hr"] = round(carbon_cost_per_hr, 4)
                result["effective_cost_per_hr"] = round(effective_cost_per_hr, 4)
                result["effective_monthly_cost"] = round(effective_cost_per_hr * gpu_count * hours, 2)
                result["carbon_intensity"] = carbon_intensity
                result["renewable_pct"] = plan.get("renewable_pct", 0)

            results.append(result)

        # Sort by effective cost (or regular cost if no carbon)
        sort_key = "effective_cost_per_hr" if include_carbon else "cost_per_gpu_hour"
        results.sort(key=lambda x: x.get(sort_key, x["cost_per_gpu_hour"]))

        return results

    def print_comparison(self, results: List[dict], include_carbon: bool = False):
        """Pretty-print the price comparison table."""
        if not results:
            print("\n  No plans found matching the criteria.")
            return

        print(f"\n  {'Rank':>4s} | {'Plan Name':38s} | {'GPU':6s} | {'Tier':12s} | "
              f"{'$/gpu/hr':>8s} | {'Monthly (1 GPU)':>15s}", end="")

        if include_carbon:
            print(f" | {'CO2 kg/hr':>10s} | {'Carbon $':>9s} | {'Eff. $/hr':>9s} | "
                  f"{'Eff. Monthly':>12s} | {'Renewable':>9s}", end="")

        print()
        print("  " + "-" * (90 if not include_carbon else 160))

        for i, r in enumerate(results, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
            print(f"  {medal} {i:>2d} | {r['name']:38s} | {r['gpu_type']:6s} | "
                  f"{r['tier']:12s} | {r['cost_per_gpu_hour']:8.2f} | "
                  f"{r['monthly_cost']:15.2f}", end="")

            if include_carbon:
                print(f" | {r.get('co2_per_gpu_hr_kg', 0):10.4f} | "
                      f"{r.get('carbon_cost_per_hr', 0):9.4f} | "
                      f"{r.get('effective_cost_per_hr', 0):9.4f} | "
                      f"{r.get('effective_monthly_cost', 0):12.2f} | "
                      f"{r.get('renewable_pct', 0):8.1f}%", end="")

            print()

        # Best value recommendation
        if results:
            best = results[0]
            print(f"\n  💡 Best value: {best['name']} at ${best['cost_per_gpu_hour']:.2f}/gpu/hr", end="")
            if include_carbon:
                print(f" (effective: ${best.get('effective_cost_per_hr', best['cost_per_gpu_hour']):.2f}/gpu/hr "
                      f"with carbon)", end="")
            print()

    def compare_tiers(self, gpu_type: str = "H100"):
        """Compare pricing across tiers for a given GPU type."""
        print(f"\n  📊 Tier Comparison for {gpu_type}")
        print("  " + "=" * 60)

        tiers = ["community", "enterprise", "sovereign"]
        for tier in tiers:
            results = self.compare_prices(gpu_type=gpu_type, tier=tier)
            if results:
                plan = results[0]
                print(f"  {tier:12s}: ${plan['cost_per_gpu_hour']:.2f}/gpu/hr — {plan['name']}")
            else:
                print(f"  {tier:12s}: No plans available")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HarchOS Price Comparison")
    parser.add_argument("--gpu-type", type=str, default=None,
                        help="Filter by GPU type (H100, A100, L40S)")
    parser.add_argument("--tier", type=str, default=None,
                        help="Filter by tier (community, enterprise, sovereign)")
    parser.add_argument("--hours", type=float, default=730.0,
                        help="Monthly hours (default: 730 = full month)")
    parser.add_argument("--gpu-count", type=int, default=1,
                        help="Number of GPUs for cost calculation")
    parser.add_argument("--include-carbon", action="store_true",
                        help="Include carbon cost in effective price")
    parser.add_argument("--compare-tiers", action="store_true",
                        help="Compare tiers for a GPU type")
    args = parser.parse_args()

    comparator = PriceComparator()

    print("=" * 60)
    print("HarchOS Price Comparison")
    print("=" * 60)

    if args.compare_tiers:
        comparator.compare_tiers(gpu_type=args.gpu_type or "H100")
        return

    results = comparator.compare_prices(
        gpu_type=args.gpu_type,
        tier=args.tier,
        hours=args.hours,
        gpu_count=args.gpu_count,
        include_carbon=args.include_carbon,
    )

    comparator.print_comparison(results, include_carbon=args.include_carbon)

    if args.include_carbon:
        print("\n  🌍 Carbon-adjusted pricing includes estimated social cost of carbon")
        print("     at $50/tonne CO2, based on ~0.3 kWh/GPU-hour consumption.")


if __name__ == "__main__":
    main()
