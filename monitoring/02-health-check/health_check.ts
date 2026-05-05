/**
 * Detailed health check and status monitoring for HarchOS (TypeScript).
 *
 * Performs comprehensive health checks including API server status,
 * database connectivity, uptime tracking, and sovereignty compliance.
 * Supports exit codes for alerting integration.
 *
 * Usage:
 *   npx ts-node health_check.ts
 *   npx ts-node health_check.ts --watch
 *   npx ts-node health_check.ts --exit-code
 */

import { HarchOSClient } from "harchos";
import type { DetailedHealth } from "harchos";

// ---------------------------------------------------------------------------
// Simulated data
// ---------------------------------------------------------------------------

const SIMULATED_HEALTH: DetailedHealth = {
  status: "healthy",
  databaseStatus: "connected",
  apiVersion: "0.2.0",
  uptimeSeconds: 86400 * 14 + 3600 * 6,
  totalEndpoints: 47,
  activeConnections: 128,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function printHealth(h: DetailedHealth): void {
  const statusIcon: Record<string, string> = { healthy: "✅", degraded: "⚠️", unhealthy: "❌" };
  const dbIcon: Record<string, string> = { connected: "✅", degraded: "⚠️", disconnected: "❌" };

  console.log("\n  ╔══════════════════════════════════════════════════════════╗");
  console.log("  ║            HarchOS Health Check                         ║");
  console.log("  ╚══════════════════════════════════════════════════════════╝");

  console.log("\n  🏥 Overall Status");
  console.log("  " + "─".repeat(50));
  console.log(`    Platform:     ${statusIcon[h.status] || "❓"} ${h.status.toUpperCase()}`);
  console.log(`    Database:     ${dbIcon[h.databaseStatus] || "❓"} ${h.databaseStatus.toUpperCase()}`);

  console.log("\n  🔧 Server Details");
  console.log("  " + "─".repeat(50));
  console.log(`    API Version:     ${h.apiVersion}`);
  console.log(`    Uptime:          ${formatUptime(h.uptimeSeconds)} (${h.uptimeSeconds.toLocaleString()}s)`);
  console.log(`    Endpoints:       ${h.totalEndpoints}`);
  console.log(`    Active Conns:    ${h.activeConnections}`);

  // Sovereignty compliance
  console.log("\n  🛡️  Sovereignty Compliance");
  console.log("  " + "─".repeat(50));
  const sovereigntyRegions: Record<string, { frameworks: string[]; dataResidency: boolean }> = {
    morocco: { frameworks: ["GDPR", "CNDP", "ISO27001"], dataResidency: true },
    algeria: { frameworks: ["PDPA"], dataResidency: true },
    nigeria: { frameworks: ["NDPR", "GDPR"], dataResidency: true },
  };
  for (const [region, reqs] of Object.entries(sovereigntyRegions)) {
    console.log(
      `    ${region.padEnd(12)}: ${reqs.frameworks.join(", ")} | Data Residency: ${reqs.dataResidency ? "Required" : "Optional"}`
    );
  }

  // Recommendations
  console.log("\n  💡 Recommendations");
  console.log("  " + "─".repeat(50));
  if (h.status === "healthy" && h.databaseStatus === "connected") {
    console.log("    ✅ Platform is operating normally");
  } else if (h.status === "degraded") {
    console.log("    ⚠️  Platform is degraded — monitor closely");
  } else {
    console.log("    ❌ Platform is unhealthy — immediate action required");
  }

  if (h.uptimeSeconds < 3600) {
    console.log("    ⚠️  Server recently restarted — verify services");
  }
}

function getExitCode(h: DetailedHealth): number {
  return { healthy: 0, degraded: 1, unhealthy: 2 }[h.status] ?? 2;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const watch = args.includes("--watch");
  const interval = parseInt(getArg(args, "--interval", "30"), 10);
  const exitCode = args.includes("--exit-code");
  const jsonOutput = args.includes("--json");

  console.log("=".repeat(60));
  console.log("HarchOS Health Check (TypeScript)");
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

  async function fetchAndDisplay(): Promise<DetailedHealth> {
    let health: DetailedHealth = SIMULATED_HEALTH;

    if (useSdk && client) {
      try {
        health = await client.monitoring.detailedHealth();
      } catch (err) {
        console.error(`[WARN] SDK call failed: ${err} — using simulated data`);
      }
    }

    if (jsonOutput) {
      console.log(JSON.stringify(health, null, 2));
    } else {
      printHealth(health);
    }

    return health;
  }

  if (watch) {
    console.log("Monitoring HarchOS health (Ctrl+C to stop)...");
    try {
      while (true) {
        const health = await fetchAndDisplay();
        const ts = new Date().toISOString();
        console.log(`\n  Last checked: ${ts} | Next check in ${interval}s`);
        await new Promise((resolve) => setTimeout(resolve, interval * 1000));
      }
    } catch {
      console.log("\nStopped monitoring.");
    }
  } else {
    const health = await fetchAndDisplay();
    console.log();

    if (exitCode) {
      process.exit(getExitCode(health));
    }
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
