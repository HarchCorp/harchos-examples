/**
 * Cost estimation for HarchOS GPU workloads (TypeScript).
 *
 * Calculates cost estimates for different GPU types, regions, and tiers
 * using the HarchOS JS SDK. Demonstrates how to plan spending before
 * deploying workloads — a key best practice for managing GPU budgets.
 *
 * Usage:
 *   npx ts-node cost_estimate.ts
 *   HARCHOS_API_KEY=hsk_... npx ts-node cost_estimate.ts --gpu-type H100 --gpu-count 8
 */

import { HarchOSClient } from "harchos";
import type {
  PricingPlan,
  CostEstimate,
  EstimateCostParams,
} from "harchos";

// ---------------------------------------------------------------------------
// Simulated pricing data (for local testing without a live server)
// ---------------------------------------------------------------------------

const SIMULATED_PLANS: PricingPlan[] = [
  {
    id: "plan-h100-ouarzazate",
    name: "H100 Enterprise (Ouarzazate)",
    gpuType: "H100",
    pricePerGpuHour: 2.1,
    pricePerCpuCoreHour: 0.04,
    pricePerGbStorageMonth: 0.08,
    pricePerGbMemoryHour: 0.005,
    currency: "USD",
    region: "morocco",
    tier: "enterprise",
    isDefault: true,
  },
  {
    id: "plan-a100-tanger",
    name: "A100 Performance (Tanger)",
    gpuType: "A100",
    pricePerGpuHour: 1.8,
    pricePerCpuCoreHour: 0.035,
    pricePerGbStorageMonth: 0.07,
    pricePerGbMemoryHour: 0.004,
    currency: "USD",
    region: "morocco",
    tier: "enterprise",
    isDefault: false,
  },
  {
    id: "plan-l40s-dakhla",
    name: "L40S Enterprise (Dakhla)",
    gpuType: "L40S",
    pricePerGpuHour: 1.4,
    pricePerCpuCoreHour: 0.03,
    pricePerGbStorageMonth: 0.06,
    pricePerGbMemoryHour: 0.003,
    currency: "USD",
    region: "morocco",
    tier: "enterprise",
    isDefault: false,
  },
];

interface SimulatedEstimate {
  gpuCount: number;
  gpuType: string;
  hours: number;
  region: string;
  tier: string;
  estimatedTotal: number;
  currency: string;
  breakdown: {
    gpuCost: number;
    cpuCost: number;
    memoryCost: number;
    storageCost: number;
    networkCost: number;
    discountPercentage: number;
    subtotal: number;
    tax: number;
  };
}

/** Compute a simulated cost estimate from local plan data. */
function simulatedEstimateCost(
  params: EstimateCostParams
): SimulatedEstimate {
  const matching = SIMULATED_PLANS.filter(
    (p) => p.gpuType === params.gpuType
  );
  const plan = matching[0] || SIMULATED_PLANS[0];

  const gpuCost = plan.pricePerGpuHour * params.gpuCount * params.hours;
  let discount = 0;
  if (plan.tier === "enterprise" && params.gpuCount >= 8) {
    discount = 5;
  }
  const subtotal = gpuCost * (1 - discount / 100);

  return {
    gpuCount: params.gpuCount,
    gpuType: params.gpuType,
    hours: params.hours,
    region: params.region || plan.region as string,
    tier: params.tier || plan.tier,
    estimatedTotal: Math.round(subtotal * 100) / 100,
    currency: plan.currency,
    breakdown: {
      gpuCost: Math.round(gpuCost * 100) / 100,
      cpuCost: 0,
      memoryCost: 0,
      storageCost: 0,
      networkCost: 0,
      discountPercentage: discount,
      subtotal: Math.round(subtotal * 100) / 100,
      tax: Math.round(subtotal * 0.2 * 100) / 100, // 20% VAT (Morocco)
    },
  };
}

// ---------------------------------------------------------------------------
// Pretty printing
// ---------------------------------------------------------------------------

function printEstimate(est: SimulatedEstimate | CostEstimate): void {
  const bd = "breakdown" in est ? est.breakdown : (est as any).breakdown;
  console.log(`  GPU:       ${est.gpuCount}x ${est.gpuType}`);
  console.log(`  Hours:     ${est.hours}`);
  console.log(`  Region:    ${est.region}`);
  console.log(`  Tier:      ${est.tier}`);
  console.log(`  Currency:  ${est.currency}`);
  console.log();
  console.log(`  ┌──────────────────────────────────────────────┐`);
  console.log(`  │ GPU Compute:      ${bd.gpuCost.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  │ CPU Compute:      ${bd.cpuCost.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  │ Memory:           ${bd.memoryCost.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  │ Storage:          ${bd.storageCost.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  │ Network:          ${bd.networkCost.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  if (bd.discountPercentage > 0) {
    console.log(`  │ Discount:         ${bd.discountPercentage.toFixed(1).padStart(9)}%              │`);
  }
  console.log(`  │ Subtotal:         ${bd.subtotal.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  │ Tax (VAT):        ${bd.tax.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  ├──────────────────────────────────────────────┤`);
  console.log(`  │ ESTIMATED TOTAL:  ${est.estimatedTotal.toFixed(2).padStart(10)} ${est.currency.padEnd(3)}           │`);
  console.log(`  └──────────────────────────────────────────────┘`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const gpuType = getArg(args, "--gpu-type", "H100");
  const gpuCount = parseInt(getArg(args, "--gpu-count", "4"), 10);
  const hours = parseFloat(getArg(args, "--hours", "24"));
  const region = getArg(args, "--region", "morocco");
  const tier = getArg(args, "--tier", "") || undefined;
  const budget = parseFloat(getArg(args, "--budget", "0")) || undefined;
  const compare = args.includes("--compare");

  console.log("=".repeat(60));
  console.log("HarchOS Cost Estimator (TypeScript)");
  console.log("=".repeat(60));

  // Try using SDK, fall back to simulated data
  let useSdk = false;
  let client: HarchOSClient | null = null;

  try {
    const apiKey = process.env.HARCHOS_API_KEY || "";
    if (apiKey) {
      client = new HarchOSClient({ apiKey });
      useSdk = true;
    }
  } catch {
    console.log("[WARN] HarchOS SDK not configured — using simulated data");
  }

  if (compare) {
    console.log("\n📊 Comparing costs across GPU types...");
    console.log(`   Configuration: ${gpuCount} GPUs, ${hours}h, ${region}`);

    const gpuTypes = ["H100", "A100", "L40S"];

    for (const gt of gpuTypes) {
      let est: SimulatedEstimate | CostEstimate;

      if (useSdk && client) {
        try {
          est = await client.pricing.estimateCost({
            gpuCount,
            gpuType: gt,
            hours,
            region,
            tier,
          });
        } catch (err) {
          console.error(`  ❌ ${gt} estimation failed: ${err}`);
          continue;
        }
      } else {
        est = simulatedEstimateCost({ gpuCount, gpuType: gt, hours, region, tier });
      }

      const perGpuHr = est.breakdown.gpuCost / Math.max(est.gpuCount * est.hours, 1);
      console.log(
        `   ${gt.padEnd(6)}: ${est.estimatedTotal.toFixed(2).padStart(10)} ${est.currency} total ` +
        `(${perGpuHr.toFixed(2)} ${est.currency}/gpu/hr)`
      );
      printEstimate(est);
    }
  } else {
    console.log(
      `\n💰 Estimating cost for ${gpuCount}x ${gpuType} ` +
      `for ${hours}h in ${region}...`
    );

    let est: SimulatedEstimate | CostEstimate;

    if (useSdk && client) {
      try {
        est = await client.pricing.estimateCost({
          gpuCount,
          gpuType,
          hours,
          region,
          tier,
        });
      } catch (err) {
        console.error(`Cost estimation failed: ${err}`);
        return;
      }
    } else {
      est = simulatedEstimateCost({ gpuCount, gpuType, hours, region, tier });
    }

    printEstimate(est);

    // Budget check
    if (budget && est.estimatedTotal > budget) {
      console.log(`\n  ❌ Exceeds budget ($${budget.toFixed(2)} USD)`);
      console.log(`     Consider using a different GPU type or fewer GPUs`);
    } else if (budget) {
      console.log(`\n  ✅ Within budget ($${budget.toFixed(2)} USD)`);
    }
  }
}

/** Simple CLI argument parser. */
function getArg(args: string[], flag: string, defaultValue: string): string {
  const idx = args.indexOf(flag);
  if (idx !== -1 && idx + 1 < args.length) {
    return args[idx + 1];
  }
  return defaultValue;
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
