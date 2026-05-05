/**
 * Platform-wide metrics display for HarchOS (TypeScript).
 *
 * Fetches and displays aggregate metrics from the HarchOS Monitoring API,
 * including GPU utilization, energy consumption, and carbon impact.
 *
 * Usage:
 *   npx ts-node platform_metrics.ts
 *   npx ts-node platform_metrics.ts --watch
 *   HARCHOS_API_KEY=hsk_... npx ts-node platform_metrics.ts
 */

import { HarchOSClient } from "harchos";
import type { PlatformMetrics } from "harchos";

// ---------------------------------------------------------------------------
// Simulated metrics
// ---------------------------------------------------------------------------

const SIMULATED_METRICS: PlatformMetrics = {
  totalHubs: 5,
  totalGpus: 1798,
  availableGpus: 423,
  gpuUtilizationPercent: 76.5,
  totalWorkloads: 1247,
  activeWorkloads: 89,
  totalEnergyKwh: 345678.5,
  avgRenewablePercentage: 81.52,
  avgCarbonIntensity: 47.0,
  avgPue: 1.12,
  totalCo2SavedKg: 12456.3,
};

// ---------------------------------------------------------------------------
// Display helpers
// ---------------------------------------------------------------------------

function categorizeUtilization(pct: number): string {
  if (pct >= 90) return "critical";
  if (pct >= 75) return "high";
  if (pct >= 50) return "moderate";
  return "low";
}

function progressBar(value: number, max: number, width = 30, fill = "█"): string {
  const pct = Math.min(value / max, 1.0);
  const filled = Math.round(pct * width);
  const empty = width - filled;
  return `[${fill.repeat(filled)}${"░".repeat(empty)}] ${(pct * 100).toFixed(1)}%`;
}

function printMetrics(m: PlatformMetrics): void {
  const used = m.totalGpus - m.availableGpus;
  const health = categorizeUtilization(m.gpuUtilizationPercent);
  const healthIcon: Record<string, string> = {
    low: "🟢", moderate: "🟡", high: "🟠", critical: "🔴",
  };
  const carbonIcon = m.avgCarbonIntensity <= 100 ? "🟢" : m.avgCarbonIntensity <= 200 ? "🟡" : "🔴";
  const pueRating = m.avgPue <= 1.2 ? "Excellent" : m.avgPue <= 1.5 ? "Good" : "Needs Improvement";

  console.log("\n  ╔══════════════════════════════════════════════════════════╗");
  console.log("  ║              HarchOS Platform Metrics                   ║");
  console.log("  ╚══════════════════════════════════════════════════════════╝");

  console.log("\n  🖥️  GPU Infrastructure");
  console.log("  " + "─".repeat(50));
  console.log(`    Total Hubs:          ${m.totalHubs.toString().padStart(8)}`);
  console.log(`    Total GPUs:          ${m.totalGpus.toString().padStart(8)}`);
  console.log(`    Available GPUs:      ${m.availableGpus.toString().padStart(8)}`);
  console.log(`    In-Use GPUs:         ${used.toString().padStart(8)}`);
  console.log(`    Utilization:         ${m.gpuUtilizationPercent.toFixed(1).padStart(7)}%  ${healthIcon[health] || "⚪"} ${health}`);
  console.log(`    ${progressBar(m.gpuUtilizationPercent, 100)}`);

  console.log("\n  📋 Workloads");
  console.log("  " + "─".repeat(50));
  console.log(`    Total Created:       ${m.totalWorkloads.toString().padStart(8)}`);
  console.log(`    Currently Active:    ${m.activeWorkloads.toString().padStart(8)}`);

  console.log("\n  ⚡ Energy & Carbon");
  console.log("  " + "─".repeat(50));
  console.log(`    Total Energy:        ${m.totalEnergyKwh.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kWh`);
  console.log(`    Renewable Share:     ${m.avgRenewablePercentage.toFixed(1).padStart(7)}%`);
  console.log(`    ${progressBar(m.avgRenewablePercentage, 100, 30, "🌱")}`);
  console.log(`    Avg Carbon Intensity:${m.avgCarbonIntensity.toFixed(1).padStart(7)} gCO2/kWh`);
  console.log(`    Carbon Rating:       ${carbonIcon}`);
  console.log(`    Avg PUE:             ${m.avgPue.toFixed(2).padStart(7)}`);
  console.log(`    PUE Rating:          ${pueRating}`);
  console.log(`    CO2 Saved:           ${m.totalCo2SavedKg.toLocaleString("en", { maximumFractionDigits: 1 }).padStart(10)} kg`);
  console.log(`    CO2 Saved (tonnes):  ${(m.totalCo2SavedKg / 1000).toFixed(2).padStart(10)} t`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const watch = args.includes("--watch");
  const interval = parseInt(getArg(args, "--interval", "30"), 10);
  const jsonOutput = args.includes("--json");

  console.log("=".repeat(60));
  console.log("HarchOS Platform Metrics (TypeScript)");
  console.log("=".repeat(60));

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

  async function fetchAndDisplay(): Promise<void> {
    let metrics: PlatformMetrics = SIMULATED_METRICS;

    if (useSdk && client) {
      try {
        metrics = await client.monitoring.metrics();
      } catch (err) {
        console.error(`[WARN] SDK call failed: ${err} — using simulated data`);
      }
    }

    if (jsonOutput) {
      console.log(JSON.stringify(metrics, null, 2));
    } else {
      printMetrics(metrics);
    }
  }

  if (watch) {
    console.log("Watching platform metrics (Ctrl+C to stop)...");
    try {
      while (true) {
        await fetchAndDisplay();
        const ts = new Date().toISOString();
        console.log(`\n  Last updated: ${ts} | Next refresh in ${interval}s`);
        await new Promise((resolve) => setTimeout(resolve, interval * 1000));
      }
    } catch {
      console.log("\nStopped watching.");
    }
  } else {
    await fetchAndDisplay();
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
