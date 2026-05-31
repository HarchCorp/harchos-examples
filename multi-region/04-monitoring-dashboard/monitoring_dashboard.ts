/**
 * Cross-region monitoring dashboard for HarchOS (TypeScript).
 *
 * Unified monitoring combining platform health, region status,
 * hub details, carbon metrics, and alerting.
 *
 * Usage:
 *   npx ts-node monitoring_dashboard.ts
 *   npx ts-node monitoring_dashboard.ts --watch
 *   HARCHOS_API_KEY=hsk_... npx ts-node monitoring_dashboard.ts
 */

import HarchOS from "@harchos/sdk";
import type { PlatformMetrics, DetailedHealth, Region } from "harchos";

// ---------------------------------------------------------------------------
// Simulated data
// ---------------------------------------------------------------------------

interface HubDetail {
  name: string;
  region: string;
  gpus: number;
  availableGpus: number;
  utilization: number;
  carbonIntensity: number;
  renewablePct: number;
  status: string;
  workloads: number;
}

const SIMULATED_HUBS: HubDetail[] = [
  { name: "Harch Ouarzazate", region: "morocco", gpus: 800, availableGpus: 180, utilization: 77.5, carbonIntensity: 18, renewablePct: 97.2, status: "healthy", workloads: 45 },
  { name: "Harch Dakhla", region: "morocco", gpus: 400, availableGpus: 95, utilization: 76.3, carbonIntensity: 32, renewablePct: 94.8, status: "healthy", workloads: 22 },
  { name: "Harch Benguerir", region: "morocco", gpus: 350, availableGpus: 82, utilization: 76.6, carbonIntensity: 55, renewablePct: 88.5, status: "healthy", workloads: 18 },
  { name: "Harch Tanger", region: "morocco", gpus: 200, availableGpus: 48, utilization: 76.0, carbonIntensity: 95, renewablePct: 82.1, status: "healthy", workloads: 8 },
  { name: "Harch Casablanca", region: "morocco", gpus: 48, availableGpus: 18, utilization: 62.5, carbonIntensity: 210, renewablePct: 45.0, status: "degraded", workloads: 3 },
];

interface Alert {
  level: "critical" | "warning" | "info";
  source: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Dashboard rendering
// ---------------------------------------------------------------------------

function computeAlerts(hubs: HubDetail[]): Alert[] {
  const alerts: Alert[] = [];
  for (const hub of hubs) {
    if (hub.utilization >= 95) {
      alerts.push({ level: "critical", source: hub.name, message: `GPU utilization critical: ${hub.utilization.toFixed(1)}%` });
    } else if (hub.utilization >= 85) {
      alerts.push({ level: "warning", source: hub.name, message: `GPU utilization high: ${hub.utilization.toFixed(1)}%` });
    }
    if (hub.carbonIntensity >= 400) {
      alerts.push({ level: "critical", source: hub.name, message: `Carbon intensity critical: ${hub.carbonIntensity} gCO2/kWh` });
    } else if (hub.carbonIntensity >= 200) {
      alerts.push({ level: "warning", source: hub.name, message: `Carbon intensity high: ${hub.carbonIntensity} gCO2/kWh` });
    }
    if (hub.status !== "healthy") {
      alerts.push({ level: "warning", source: hub.name, message: `Hub status: ${hub.status}` });
    }
  }
  return alerts;
}

function renderDashboard(
  health: DetailedHealth,
  metrics: PlatformMetrics,
  hubs: HubDetail[],
): void {
  const statusIcon: Record<string, string> = { healthy: "✅", degraded: "⚠️", unhealthy: "❌" };
  const uptimeDays = Math.floor(health.uptimeSeconds / 86400);
  const uptimeHours = Math.floor((health.uptimeSeconds % 86400) / 3600);

  console.log("\n  ╔════════════════════════════════════════════════════════════════════╗");
  console.log("  ║          HarchOS Cross-Region Monitoring Dashboard                ║");
  console.log("  ╚════════════════════════════════════════════════════════════════════╝");

  // Platform health
  console.log(`\n  🏥 Platform Health: ${statusIcon[health.status] || "❓"} ${health.status.toUpperCase()}`);
  console.log("  " + "─".repeat(70));
  console.log(`    API Version:      ${health.apiVersion}`);
  console.log(`    Uptime:           ${uptimeDays}d ${uptimeHours}h`);
  console.log(`    Database:         ${health.databaseStatus === "connected" ? "✅ Connected" : "❌ " + health.databaseStatus}`);
  console.log(`    Endpoints:        ${health.totalEndpoints}`);
  console.log(`    Active Conns:     ${health.activeConnections}`);

  // Platform metrics
  console.log("\n  📊 Platform Summary");
  console.log("  " + "─".repeat(70));
  console.log(`    Total Hubs:       ${metrics.totalHubs}`);
  console.log(`    Total GPUs:       ${metrics.totalGpus}`);
  console.log(`    Available GPUs:   ${metrics.availableGpus}`);
  console.log(`    GPU Utilization:  ${metrics.gpuUtilizationPercent.toFixed(1)}%`);
  console.log(`    Active Workloads: ${metrics.activeWorkloads}`);
  console.log(`    Avg Renewable:    ${metrics.avgRenewablePercentage.toFixed(1)}%`);
  console.log(`    Avg Carbon:       ${metrics.avgCarbonIntensity.toFixed(1)} gCO2/kWh`);
  console.log(`    CO2 Saved:        ${metrics.totalCo2SavedKg.toLocaleString("en", { maximumFractionDigits: 1 })} kg`);

  // Hub details
  console.log("\n  🏭 Hub Details");
  console.log("  " + "─".repeat(70));
  console.log(
    `    ${"Hub".padEnd(22)} | ${"GPUs".padStart(5)} | ${"Avail".padStart(5)} | ${"Util".padStart(6)} | ` +
    `${"Carbon".padStart(8)} | ${"Renew".padStart(6)} | Status`
  );
  console.log(
    `    ${"─".repeat(22)}-+-${"─".repeat(5)}-+-${"─".repeat(5)}-+-${"─".repeat(6)}-+-` +
    `${"─".repeat(8)}-+-${"─".repeat(6)}-+-${"─".repeat(8)}`
  );

  const sortedHubs = [...hubs].sort((a, b) => a.carbonIntensity - b.carbonIntensity);
  for (const hub of sortedHubs) {
    const carbonIcon = hub.carbonIntensity <= 100 ? "🟢" : hub.carbonIntensity <= 200 ? "🟡" : "🔴";
    const statusIcon = hub.status === "healthy" ? "✅" : "⚠️";
    console.log(
      `    ${hub.name.padEnd(22)} | ${hub.gpus.toString().padStart(5)} | ${hub.availableGpus.toString().padStart(5)} | ` +
      `${hub.utilization.toFixed(1).padStart(5)}% | ${carbonIcon} ${hub.carbonIntensity.toString().padStart(4)} | ` +
      `${hub.renewablePct.toFixed(1).padStart(5)}% | ${statusIcon} ${hub.status}`
    );
  }

  // Alerts
  const alerts = computeAlerts(hubs);
  if (alerts.length) {
    console.log(`\n  🚨 Alerts (${alerts.length})`);
    console.log("  " + "─".repeat(70));
    for (const alert of alerts) {
      const icon = alert.level === "critical" ? "🔴" : "🟡";
      console.log(`    ${icon} [${alert.level.toUpperCase().padEnd(8)}] ${alert.source.padEnd(20)}: ${alert.message}`);
    }
  } else {
    console.log("\n  ✅ No active alerts");
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const watch = args.includes("--watch");
  const interval = parseInt(getArg(args, "--interval", "30"), 10);
  const jsonOutput = args.includes("--json");

  console.log("=".repeat(70));
  console.log("HarchOS Cross-Region Monitoring Dashboard (TypeScript)");
  console.log("=".repeat(70));

  let useSdk = false;
  let client: HarchOS | null = null;

  try {
    const apiKey = process.env.HARCHOS_API_KEY || "";
    if (apiKey) {
      client = new HarchOS({ apiKey });
      useSdk = true;
    }
  } catch {
    console.log("[WARN] HarchOS SDK not configured — using simulated data");
  }

  async function fetchAndDisplay(): Promise<void> {
    let health: DetailedHealth = {
      status: "healthy",
      databaseStatus: "connected",
      apiVersion: "0.2.0",
      uptimeSeconds: 86400 * 14 + 3600 * 6,
      totalEndpoints: 47,
      activeConnections: 128,
    };
    let metrics: PlatformMetrics = {
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

    if (useSdk && client) {
      try {
        health = await client.monitoring.detailedHealth();
      } catch (err) {
        console.log(`  [WARN] Health check failed: ${err}`);
      }
      try {
        metrics = await client.monitoring.metrics();
      } catch (err) {
        console.log(`  [WARN] Metrics fetch failed: ${err}`);
      }
    }

    if (jsonOutput) {
      console.log(JSON.stringify({ health, metrics, hubs: SIMULATED_HUBS }, null, 2));
    } else {
      renderDashboard(health, metrics, SIMULATED_HUBS);
    }
  }

  if (watch) {
    console.log("Monitoring (Ctrl+C to stop)...");
    try {
      while (true) {
        await fetchAndDisplay();
        const ts = new Date().toISOString();
        console.log(`\n  Last updated: ${ts} | Next refresh in ${interval}s`);
        await new Promise((resolve) => setTimeout(resolve, interval * 1000));
      }
    } catch {
      console.log("\nStopped monitoring.");
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
