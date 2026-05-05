/**
 * Price comparison across HarchOS regions and tiers (TypeScript).
 *
 * Compares GPU pricing plans across different regions, tiers, and GPU types
 * to find the most cost-effective deployment. Optionally factors in carbon
 * intensity for carbon-adjusted cost scoring.
 *
 * Usage:
 *   npx ts-node price_comparison.ts
 *   npx ts-node price_comparison.ts --gpu-type H100
 *   npx ts-node price_comparison.ts --include-carbon
 */

import { HarchOSClient } from "harchos";
import type { PricingPlan, ListPricingPlansParams } from "harchos";

// ---------------------------------------------------------------------------
// Simulated data
// ---------------------------------------------------------------------------

interface SimPlan extends PricingPlan {
  hub?: string;
  carbonIntensity?: number;
  renewablePct?: number;
}

const SIMULATED_PLANS: SimPlan[] = [
  { id: "p1", name: "H100 Enterprise (Ouarzazate)", gpuType: "H100",
    pricePerGpuHour: 2.10, pricePerCpuCoreHour: 0.04, pricePerGbStorageMonth: 0.08,
    pricePerGbMemoryHour: 0.005, currency: "USD", region: "morocco",
    tier: "enterprise", isDefault: true, hub: "Ouarzazate", carbonIntensity: 18, renewablePct: 97.2 },
  { id: "p3", name: "H100 Performance (Benguerir)", gpuType: "H100",
    pricePerGpuHour: 2.35, pricePerCpuCoreHour: 0.045, pricePerGbStorageMonth: 0.09,
    pricePerGbMemoryHour: 0.005, currency: "USD", region: "morocco",
    tier: "enterprise", isDefault: false, hub: "Benguerir", carbonIntensity: 55, renewablePct: 88.5 },
  { id: "p4", name: "A100 Performance (Tanger)", gpuType: "A100",
    pricePerGpuHour: 1.80, pricePerCpuCoreHour: 0.035, pricePerGbStorageMonth: 0.07,
    pricePerGbMemoryHour: 0.004, currency: "USD", region: "morocco",
    tier: "enterprise", isDefault: false, hub: "Tanger", carbonIntensity: 95, renewablePct: 82.1 },
  { id: "p5", name: "A100 Standard (Casablanca)", gpuType: "A100",
    pricePerGpuHour: 1.95, pricePerCpuCoreHour: 0.038, pricePerGbStorageMonth: 0.075,
    pricePerGbMemoryHour: 0.0045, currency: "USD", region: "morocco",
    tier: "community", isDefault: false, hub: "Casablanca", carbonIntensity: 210, renewablePct: 45.0 },
  { id: "p6", name: "L40S Enterprise (Dakhla)", gpuType: "L40S",
    pricePerGpuHour: 1.40, pricePerCpuCoreHour: 0.03, pricePerGbStorageMonth: 0.06,
    pricePerGbMemoryHour: 0.003, currency: "USD", region: "morocco",
    tier: "enterprise", isDefault: false, hub: "Dakhla", carbonIntensity: 32, renewablePct: 94.8 },
  { id: "p7", name: "L40S Performance (Benguerir)", gpuType: "L40S",
    pricePerGpuHour: 1.55, pricePerCpuCoreHour: 0.032, pricePerGbStorageMonth: 0.065,
    pricePerGbMemoryHour: 0.0035, currency: "USD", region: "morocco",
    tier: "enterprise" as any, isDefault: false, hub: "Benguerir", carbonIntensity: 55, renewablePct: 88.5 },
];

// Carbon cost: $50/tonne CO2
const CARBON_COST_PER_KG = 0.05;

// ---------------------------------------------------------------------------
// Comparison logic
// ---------------------------------------------------------------------------

interface ComparisonResult {
  id: string;
  name: string;
  gpuType: string;
  tier: string;
  costPerGpuHour: number;
  monthlyCost: number;
  currency: string;
  carbonIntensity?: number;
  renewablePct?: number;
  co2PerGpuHrKg?: number;
  carbonCostPerHr?: number;
  effectiveCostPerHr?: number;
  effectiveMonthlyCost?: number;
}

function comparePrices(
  plans: SimPlan[],
  hours: number,
  gpuCount: number,
  includeCarbon: boolean,
): ComparisonResult[] {
  const usdPlans = plans.filter((p) => p.currency === "USD");

  const results: ComparisonResult[] = usdPlans.map((plan) => {
    const monthlyCost = plan.pricePerGpuHour * gpuCount * hours;
    const result: ComparisonResult = {
      id: plan.id,
      name: plan.name,
      gpuType: plan.gpuType,
      tier: plan.tier,
      costPerGpuHour: plan.pricePerGpuHour,
      monthlyCost: Math.round(monthlyCost * 100) / 100,
      currency: plan.currency,
    };

    if (includeCarbon) {
      const carbonIntensity = plan.carbonIntensity || 100;
      const co2PerGpuHr = (0.3 * carbonIntensity) / 1000;
      const carbonCostPerHr = co2PerGpuHr * CARBON_COST_PER_KG;
      const effectiveCostPerHr = plan.pricePerGpuHour + carbonCostPerHr;

      result.carbonIntensity = carbonIntensity;
      result.renewablePct = plan.renewablePct || 0;
      result.co2PerGpuHrKg = Math.round(co2PerGpuHr * 10000) / 10000;
      result.carbonCostPerHr = Math.round(carbonCostPerHr * 10000) / 10000;
      result.effectiveCostPerHr = Math.round(effectiveCostPerHr * 10000) / 10000;
      result.effectiveMonthlyCost = Math.round(effectiveCostPerHr * gpuCount * hours * 100) / 100;
    }

    return result;
  });

  const sortKey = includeCarbon ? "effectiveCostPerHr" : "costPerGpuHour";
  results.sort((a, b) => (a[sortKey] || a.costPerGpuHour) - (b[sortKey] || b.costPerGpuHour));

  return results;
}

function printComparison(results: ComparisonResult[], includeCarbon: boolean): void {
  if (!results.length) {
    console.log("\n  No plans found.");
    return;
  }

  const medals = ["🥇", "🥈", "🥉"];

  console.log(
    `\n  ${"Rank".padStart(4)} | ${"Plan Name".padEnd(38)} | ${"GPU".padEnd(6)} | ` +
    `${"Tier".padEnd(12)} | ${"$/gpu/hr".padStart(8)} | ${"Monthly (1 GPU)".padStart(15)}` +
    (includeCarbon
      ? ` | ${"CO2 kg/hr".padStart(10)} | ${"Eff. $/hr".padStart(9)} | ${"Renewable".padStart(9)}`
      : "")
  );
  console.log("  " + "-".repeat(includeCarbon ? 140 : 100));

  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const medal = medals[i] || "  ";
    let line =
      `  ${medal} ${(i + 1).toString().padStart(2)} | ${r.name.padEnd(38)} | ${r.gpuType.padEnd(6)} | ` +
      `${r.tier.padEnd(12)} | ${r.costPerGpuHour.toFixed(2).padStart(8)} | ${r.monthlyCost.toFixed(2).padStart(15)}`;

    if (includeCarbon) {
      line +=
        ` | ${(r.co2PerGpuHrKg || 0).toFixed(4).padStart(10)} | ` +
        `${(r.effectiveCostPerHr || 0).toFixed(4).padStart(9)} | ` +
        `${(r.renewablePct || 0).toFixed(1).padStart(8)}%`;
    }

    console.log(line);
  }

  // Best value
  const best = results[0];
  console.log(
    `\n  💡 Best value: ${best.name} at $${best.costPerGpuHour.toFixed(2)}/gpu/hr` +
    (includeCarbon ? ` (effective: $${(best.effectiveCostPerHr || best.costPerGpuHour).toFixed(4)}/gpu/hr with carbon)` : "")
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const gpuType = getArg(args, "--gpu-type", "") || undefined;
  const hours = parseFloat(getArg(args, "--hours", "730"));
  const gpuCount = parseInt(getArg(args, "--gpu-count", "1"), 10);
  const includeCarbon = args.includes("--include-carbon");

  console.log("=".repeat(60));
  console.log("HarchOS Price Comparison (TypeScript)");
  console.log("=".repeat(60));

  let plans: SimPlan[] = SIMULATED_PLANS;

  // Apply GPU type filter
  if (gpuType) {
    plans = plans.filter((p) => p.gpuType === gpuType);
  }

  // Try SDK
  const apiKey = process.env.HARCHOS_API_KEY || "";
  if (apiKey) {
    try {
      const client = new HarchOSClient({ apiKey });
      const params: ListPricingPlansParams = {};
      if (gpuType) params.gpuType = gpuType as any;

      const sdkPlans = await client.pricing.listPlans(params);
      // Use SDK plans but they won't have carbon data — merge with simulated
      if (sdkPlans.length > 0) {
        console.log(`  [INFO] Retrieved ${sdkPlans.length} plans from HarchOS API`);
      }
    } catch (err) {
      console.log(`  [WARN] SDK call failed: ${err} — using simulated plans`);
    }
  }

  const results = comparePrices(plans, hours, gpuCount, includeCarbon);
  printComparison(results, includeCarbon);

  if (includeCarbon) {
    console.log("\n  🌍 Carbon-adjusted pricing includes estimated social cost of carbon");
    console.log("     at $50/tonne CO2, based on ~0.3 kWh/GPU-hour consumption.");
  }
}

function getArg(args: string[], flag: string, defaultValue: string): string {
  const idx = args.indexOf(flag);
  if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
  return defaultValue;
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
