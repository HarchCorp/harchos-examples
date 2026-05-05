/**
 * Carbon metrics dashboard for HarchOS (TypeScript).
 *
 * Builds a comprehensive carbon metrics dashboard combining platform
 * metrics, carbon intensity data, and carbon-aware scheduling results.
 *
 * Usage:
 *   npx ts-node carbon_dashboard.ts
 *   npx ts-node carbon_dashboard.ts --detailed
 *   npx ts-node carbon_dashboard.ts --carbon-budget 5000
 */

import { HarchOSClient } from "harchos";
import type { PlatformMetrics } from "harchos";

// ---------------------------------------------------------------------------
// Simulated data
// ---------------------------------------------------------------------------

interface HubData {
  name: string;
  region: string;
  gpus: number;
  renewablePct: number;
  carbonIntensity: number;
  activeWorkloads: number;
}

const SIMULATED_HUBS: HubData[] = [
  { name: "Harch Ouarzazate", region: "morocco", gpus: 800, renewablePct: 97.2, carbonIntensity: 18, activeWorkloads: 45 },
  { name: "Harch Dakhla", region: "morocco", gpus: 400, renewablePct: 94.8, carbonIntensity: 32, activeWorkloads: 22 },
  { name: "Harch Benguerir", region: "morocco", gpus: 350, renewablePct: 88.5, carbonIntensity: 55, activeWorkloads: 18 },
  { name: "Harch Tanger", region: "morocco", gpus: 200, renewablePct: 82.1, carbonIntensity: 95, activeWorkloads: 8 },
  { name: "Harch Casablanca", region: "morocco", gpus: 48, renewablePct: 45.0, carbonIntensity: 210, activeWorkloads: 3 },
];

const SIMULATED_METRICS: PlatformMetrics = {
  totalHubs: 5,
  totalGpus: 1798,
  availableGpus: 423,
  gpuUtilizationPercent: 76.5,
  totalWorkloads: 1247,
  activeWorkloads: 96,
  totalEnergyKwh: 345678.5,
  avgRenewablePercentage: 81.52,
  avgCarbonIntensity: 47.0,
  avgPue: 1.12,
  totalCo2SavedKg: 12456.3,
};

// ---------------------------------------------------------------------------
// Dashboard logic
// ---------------------------------------------------------------------------

const GREEN_THRESHOLD = 100;
const YELLOW_THRESHOLD = 200;
const INDUSTRY_AVG_INTENSITY = 450;

function carbonIcon(intensity: number): string {
  if (intensity <= GREEN_THRESHOLD) return "🟢";
  if (intensity <= YELLOW_THRESHOLD) return "🟡";
  return "🔴";
}

function computeCarbonSavings(metrics: PlatformMetrics) {
  const co2Industry = (metrics.totalEnergyKwh * INDUSTRY_AVG_INTENSITY) / 1000;
  const co2Harchos = (metrics.totalEnergyKwh * metrics.avgCarbonIntensity) / 1000;
  const co2Saved = co2Industry - co2Harchos;
  const savingsPct = (1 - metrics.avgCarbonIntensity / INDUSTRY_AVG_INTENSITY) * 100;

  return {
    co2IndustryKg: Math.round(co2Industry * 10) / 10,
    co2HarchosKg: Math.round(co2Harchos * 10) / 10,
    co2SavedKg: Math.round(co2Saved * 10) / 10,
    co2SavedTonnes: Math.round((co2Saved / 1000) * 100) / 100,
    savingsPercentage: Math.round(savingsPct * 10) / 10,
  };
}

function detectGreenWindows(hubs: HubData[]) {
  return hubs
    .filter((h) => h.carbonIntensity <= GREEN_THRESHOLD)
    .map((h) => ({
      hub: h.name,
      carbonIntensity: h.carbonIntensity,
      renewablePct: h.renewablePct,
      availableGpus: h.gpus - h.activeWorkloads * 8,
      status: h.carbonIntensity <= 50 ? "optimal" : "green",
    }));
}

function renderDashboard(
  metrics: PlatformMetrics,
  hubs: HubData[],
  detailed: boolean,
): void {
  const savings = computeCarbonSavings(metrics);
  const windows = detectGreenWindows(hubs);

  console.log("\n  ╔════════════════════════════════════════════════════════════════╗");
  console.log("  ║          HarchOS Carbon Metrics Dashboard                     ║");
  console.log("  ╚════════════════════════════════════════════════════════════════╝");

  // Overview
  console.log("\n  🌍 Carbon Overview");
  console.log("  " + "─".repeat(60));
  console.log(`    Average Carbon Intensity: ${metrics.avgCarbonIntensity.toFixed(1).padStart(6)} gCO2/kWh ${carbonIcon(metrics.avgCarbonIntensity)}`);
  console.log(`    Average Renewable Share:  ${metrics.avgRenewablePercentage.toFixed(1).padStart(6)}%`);
  console.log(`    Total Energy Consumed:    ${metrics.totalEnergyKwh.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kWh`);
  console.log(`    Average PUE:              ${metrics.avgPue.toFixed(2).padStart(6)}`);

  // Carbon Savings
  console.log("\n  💚 Carbon Savings (vs Industry Average)");
  console.log("  " + "─".repeat(60));
  console.log(`    Industry Average:     ${INDUSTRY_AVG_INTENSITY.toString().padStart(6)} gCO2/kWh`);
  console.log(`    HarchOS Average:      ${metrics.avgCarbonIntensity.toFixed(0).padStart(6)} gCO2/kWh`);
  console.log(`    Savings:              ${savings.savingsPercentage.toFixed(1).padStart(5)}%`);
  console.log(`    CO2 Avoided:          ${savings.co2SavedKg.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kg (${savings.co2SavedTonnes.toFixed(2)} tonnes)`);
  console.log(`    CO2 Saved (Scheduled):${metrics.totalCo2SavedKg.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kg`);

  // Hub Breakdown
  console.log("\n  🏭 Hub Carbon Breakdown");
  console.log("  " + "─".repeat(60));
  console.log(`    ${"Hub".padEnd(22)} | ${"gCO2/kWh".padStart(8)} | ${"Renewable".padStart(9)} | ${"GPUs".padStart(5)} | Status`);
  console.log(`    ${"─".repeat(22)}-+-${"─".repeat(8)}-+-${"─".repeat(9)}-+-${"─".repeat(5)}-+-${"─".repeat(10)}`);

  const sortedHubs = [...hubs].sort((a, b) => a.carbonIntensity - b.carbonIntensity);
  for (const hub of sortedHubs) {
    const icon = carbonIcon(hub.carbonIntensity);
    const status =
      hub.carbonIntensity <= 50 ? "OPTIMAL" :
      hub.carbonIntensity <= GREEN_THRESHOLD ? "GREEN" :
      hub.carbonIntensity <= YELLOW_THRESHOLD ? "ACCEPTABLE" : "AVOID";
    console.log(
      `    ${hub.name.padEnd(22)} | ${hub.carbonIntensity.toString().padStart(7)}  | ` +
      `${hub.renewablePct.toFixed(1).padStart(8)}% | ${hub.gpus.toString().padStart(5)} | ${icon} ${status}`
    );
  }

  // Green Windows
  if (windows.length) {
    console.log("\n  🌿 Current Green Windows");
    console.log("  " + "─".repeat(60));
    for (const w of windows) {
      console.log(
        `    ${carbonIcon(w.carbonIntensity)} ${w.hub.padEnd(22)} — ` +
        `${w.carbonIntensity} gCO2/kWh | ${w.renewablePct.toFixed(1)}% renewable | ` +
        `~${w.availableGpus} GPUs available | ${w.status.toUpperCase()}`
      );
    }
  }

  // Detailed
  if (detailed) {
    console.log("\n  📈 Detailed Carbon Analysis");
    console.log("  " + "─".repeat(60));

    for (const hub of hubs) {
      const gpuShare = hub.gpus / metrics.totalGpus;
      const hubEnergy = metrics.totalEnergyKwh * gpuShare;
      const hubCo2 = (hubEnergy * hub.carbonIntensity) / 1000;

      console.log(`\n    ${hub.name}:`);
      console.log(`      Estimated Energy:     ${hubEnergy.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kWh`);
      console.log(`      Estimated CO2:        ${hubCo2.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kg`);
    }

    // Equivalents
    const treesEquiv = Math.round(savings.co2SavedKg / 22);
    const carsEquiv = (savings.co2SavedKg / 4600).toFixed(1);
    console.log("\n    Carbon Equivalents:");
    console.log(`      CO2 saved = ${treesEquiv.toLocaleString()} trees absorbing for 1 year`);
    console.log(`      CO2 saved = ${carsEquiv} cars off the road for 1 year`);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const detailed = args.includes("--detailed");
  const carbonBudget = parseFloat(getArg(args, "--carbon-budget", "0")) || undefined;
  const jsonOutput = args.includes("--json");

  console.log("=".repeat(60));
  console.log("HarchOS Carbon Dashboard (TypeScript)");
  console.log("=".repeat(60));

  let metrics: PlatformMetrics = SIMULATED_METRICS;
  let hubs: HubData[] = SIMULATED_HUBS;

  // Try SDK
  const apiKey = process.env.HARCHOS_API_KEY || "";
  if (apiKey) {
    try {
      const client = new HarchOSClient({ apiKey });
      metrics = await client.monitoring.metrics();
      console.log("  [INFO] Using live metrics from HarchOS API");
    } catch (err) {
      console.log(`  [WARN] SDK call failed: ${err} — using simulated data`);
    }
  }

  if (jsonOutput) {
    console.log(JSON.stringify({ metrics, hubs }, null, 2));
  } else {
    renderDashboard(metrics, hubs, detailed);

    // Carbon budget check
    if (carbonBudget) {
      const savings = computeCarbonSavings(metrics);
      const withinBudget = savings.co2HarchosKg <= carbonBudget;

      console.log("\n  💰 Carbon Budget Check");
      console.log("  " + "─".repeat(60));
      console.log(`    Carbon Budget:    ${carbonBudget.toLocaleString().padStart(10)} kg CO2`);
      console.log(`    Current Emissions:${savings.co2HarchosKg.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kg CO2`);
      console.log(`    Budget Used:      ${((savings.co2HarchosKg / carbonBudget) * 100).toFixed(1).padStart(9)}%`);

      if (withinBudget) {
        console.log("    ✅ Within carbon budget");
      } else {
        console.log("    ❌ Over carbon budget");
        console.log("    💡 Consider scheduling workloads during green windows");
      }
    }

    console.log();
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
