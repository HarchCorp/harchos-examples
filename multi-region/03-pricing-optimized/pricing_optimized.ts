/**
 * Pricing-optimized multi-region deployment for HarchOS (TypeScript).
 *
 * Deploys workloads across regions optimized for cost while respecting
 * carbon intensity thresholds and sovereignty requirements.
 *
 * Usage:
 *   npx ts-node pricing_optimized.ts --gpu-type H100 --gpu-count 8 --hours 168
 *   npx ts-node pricing_optimized.ts --carbon-max 100
 */

import HarchOS from "@harchos/sdk";
import type { Region, PricingPlan, EstimateCostParams } from "harchos";

// ---------------------------------------------------------------------------
// Simulated data
// ---------------------------------------------------------------------------

interface HubInfo {
  name: string;
  region: string;
  gpus: number;
  renewablePct: number;
  carbonIntensity: number;
  gpuType: string;
  pricePerGpuHour: number;
  tier: string;
}

const SIMULATED_HUBS: HubInfo[] = [
  { name: "Harch Ouarzazate", region: "morocco", gpus: 800, renewablePct: 97.2, carbonIntensity: 18, gpuType: "H100", pricePerGpuHour: 2.10, tier: "enterprise" },
  { name: "Harch Dakhla", region: "morocco", gpus: 400, renewablePct: 94.8, carbonIntensity: 32, gpuType: "L40S", pricePerGpuHour: 1.40, tier: "enterprise" },
  { name: "Harch Benguerir", region: "morocco", gpus: 350, renewablePct: 88.5, carbonIntensity: 55, gpuType: "H100", pricePerGpuHour: 2.35, tier: "performance" },
  { name: "Harch Tanger", region: "morocco", gpus: 200, renewablePct: 82.1, carbonIntensity: 95, gpuType: "A100", pricePerGpuHour: 1.80, tier: "enterprise" },
  { name: "Harch Casablanca", region: "morocco", gpus: 48, renewablePct: 45.0, carbonIntensity: 210, gpuType: "A100", pricePerGpuHour: 1.95, tier: "community" },
];

const SOVEREIGNTY_RULES: Record<string, { frameworks: string[]; dataResidency: boolean }> = {
  morocco: { frameworks: ["GDPR", "CNDP"], dataResidency: true },
  nigeria: { frameworks: ["NDPR"], dataResidency: true },
  kenya: { frameworks: ["PDPA"], dataResidency: true },
};

// ---------------------------------------------------------------------------
// Logic
// ---------------------------------------------------------------------------

interface DeploymentRecommendation {
  recommendation: "deploy" | "relax_constraints" | "no_suitable_hub";
  hub?: string;
  region?: string;
  gpuType?: string;
  gpuCount?: number;
  pricePerGpuHour?: number;
  carbonIntensity?: number;
  renewablePct?: number;
  estimatedCost?: number;
  hours?: number;
  tier?: string;
  alternatives?: Array<{
    hub: string;
    pricePerGpuHour: number;
    carbonIntensity: number;
    estimatedCost: number;
  }>;
  sovereignty?: { frameworks: string[]; dataResidency: boolean };
  reason?: string;
  suggestion?: string;
}

function getEligibleHubs(
  gpuType: string,
  gpuCount: number,
  carbonMax: number,
  tier?: string,
  sovereignOnly?: boolean,
): HubInfo[] {
  let eligible = SIMULATED_HUBS.filter((h) => {
    if (h.gpuType !== gpuType) return false;
    if (h.gpus < gpuCount) return false;
    if (h.carbonIntensity > carbonMax) return false;
    if (tier && h.tier !== tier) return false;
    if (sovereignOnly) {
      const rules = SOVEREIGNTY_RULES[h.region];
      if (!rules?.dataResidency) return false;
    }
    return true;
  });

  eligible.sort((a, b) => a.pricePerGpuHour - b.pricePerGpuHour);
  return eligible;
}

function recommend(
  gpuType: string,
  gpuCount: number,
  hours: number,
  carbonMax: number,
  tier?: string,
  sovereignOnly?: boolean,
): DeploymentRecommendation {
  const eligible = getEligibleHubs(gpuType, gpuCount, carbonMax, tier, sovereignOnly);

  if (!eligible.length) {
    const allMatching = SIMULATED_HUBS.filter(
      (h) => h.gpuType === gpuType && h.gpus >= gpuCount
    );
    if (allMatching.length) {
      const cheapest = allMatching.reduce((a, b) =>
        a.pricePerGpuHour < b.pricePerGpuHour ? a : b
      );
      return {
        recommendation: "relax_constraints",
        reason: `No hubs within carbon limit (${carbonMax} gCO2/kWh)`,
        suggestion: `Increase --carbon-max to at least ${cheapest.carbonIntensity}`,
      };
    }
    return {
      recommendation: "no_suitable_hub",
      reason: `No hubs with ${gpuCount}x ${gpuType} GPUs available`,
    };
  }

  const best = eligible[0];
  const estimatedCost = best.pricePerGpuHour * gpuCount * hours;

  return {
    recommendation: "deploy",
    hub: best.name,
    region: best.region,
    gpuType: best.gpuType,
    gpuCount,
    pricePerGpuHour: best.pricePerGpuHour,
    carbonIntensity: best.carbonIntensity,
    renewablePct: best.renewablePct,
    estimatedCost: Math.round(estimatedCost * 100) / 100,
    hours,
    tier: best.tier,
    alternatives: eligible.slice(1).map((h) => ({
      hub: h.name,
      pricePerGpuHour: h.pricePerGpuHour,
      carbonIntensity: h.carbonIntensity,
      estimatedCost: Math.round(h.pricePerGpuHour * gpuCount * hours * 100) / 100,
    })),
    sovereignty: SOVEREIGNTY_RULES[best.region],
  };
}

function printRecommendation(rec: DeploymentRecommendation): void {
  if (rec.recommendation === "no_suitable_hub") {
    console.log(`\n  ❌ ${rec.reason}`);
    return;
  }

  if (rec.recommendation === "relax_constraints") {
    console.log(`\n  ⚠️  ${rec.reason}`);
    console.log(`     Suggestion: ${rec.suggestion}`);
    return;
  }

  console.log("\n  🎯 Deployment Recommendation");
  console.log("  " + "─".repeat(60));
  console.log(`    Hub:               ${rec.hub}`);
  console.log(`    Region:            ${rec.region}`);
  console.log(`    GPU:               ${rec.gpuCount}x ${rec.gpuType}`);
  console.log(`    Tier:              ${rec.tier}`);
  console.log(`    Duration:          ${rec.hours} hours`);
  console.log(`    Price/GPU/hr:      $${rec.pricePerGpuHour?.toFixed(2)}`);
  console.log(`    Carbon Intensity:  ${rec.carbonIntensity} gCO2/kWh`);
  console.log(`    Renewable:         ${rec.renewablePct?.toFixed(1)}%`);
  console.log(`    Estimated Cost:    $${rec.estimatedCost?.toFixed(2)} USD`);

  if (rec.sovereignty) {
    console.log("\n  🛡️  Sovereignty");
    console.log(`    Data Residency:    ${rec.sovereignty.dataResidency ? "Required ✅" : "Optional"}`);
    if (rec.sovereignty.frameworks.length) {
      console.log(`    Compliance:        ${rec.sovereignty.frameworks.join(", ")}`);
    }
  }

  if (rec.alternatives?.length) {
    console.log("\n  🔄 Alternatives (sorted by price)");
    console.log("  " + "─".repeat(60));
    for (const alt of rec.alternatives) {
      const icon = alt.carbonIntensity <= 100 ? "🟢" : alt.carbonIntensity <= 200 ? "🟡" : "🔴";
      console.log(
        `    ${icon} ${alt.hub.padEnd(25)} | ` +
        `$${alt.pricePerGpuHour.toFixed(2)}/gpu/hr | ` +
        `${alt.carbonIntensity} gCO2/kWh | ` +
        `$${alt.estimatedCost.toFixed(2)}`
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const gpuType = getArg(args, "--gpu-type", "H100");
  const gpuCount = parseInt(getArg(args, "--gpu-count", "4"), 10);
  const hours = parseFloat(getArg(args, "--hours", "24"));
  const carbonMax = parseFloat(getArg(args, "--carbon-max", "200"));
  const tier = getArg(args, "--tier", "") || undefined;
  const sovereignOnly = args.includes("--sovereign-only");

  console.log("=".repeat(60));
  console.log("HarchOS Pricing-Optimized Deployment (TypeScript)");
  console.log("=".repeat(60));

  // Try SDK for regions
  const apiKey = process.env.HARCHOS_API_KEY || "";
  if (apiKey) {
    try {
      const client = new HarchOS({ apiKey });
      const regions = await client.regions.list({ available: true });
      console.log(`\n  📍 Available Regions (from API): ${regions.length}`);
      for (const r of regions) {
        console.log(`    • ${r.name} (${r.code}): ${r.hubCount} hubs, ${r.totalGpus} GPUs`);
      }
    } catch (err) {
      console.log(`  [WARN] SDK call failed: ${err}`);
    }
  }

  console.log(`\n  🔍 Finding best hub for ${gpuCount}x ${gpuType} (${hours}h, carbon ≤ ${carbonMax} gCO2/kWh)...`);

  const rec = recommend(gpuType, gpuCount, hours, carbonMax, tier, sovereignOnly);
  printRecommendation(rec);
  console.log();
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
