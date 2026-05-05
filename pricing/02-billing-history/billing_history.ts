/**
 * Billing history viewer for HarchOS GPU workloads (TypeScript).
 *
 * Retrieves and displays billing records from the HarchOS platform
 * using the JS SDK. Shows filtering by status and date range, and
 * computes spending summaries with overdue alerts.
 *
 * Usage:
 *   npx ts-node billing_history.ts
 *   npx ts-node billing_history.ts --status overdue
 *   HARCHOS_API_KEY=hsk_... npx ts-node billing_history.ts
 */

import { HarchOSClient } from "harchos";
import type { BillingRecord, ListBillingRecordsParams } from "harchos";

// ---------------------------------------------------------------------------
// Simulated billing data
// ---------------------------------------------------------------------------

interface SimulatedRecord {
  id: string;
  userId: string;
  workloadId: string;
  hubId: string;
  gpuHours: number;
  cpuCoreHours: number;
  memoryGbHours: number;
  storageGbMonths: number;
  totalCost: number;
  currency: string;
  status: "open" | "closed" | "paid" | "overdue";
  periodStart: string;
  periodEnd: string;
}

const SIMULATED_RECORDS: SimulatedRecord[] = [
  {
    id: "bill-001",
    userId: "user-alice",
    workloadId: "wkld-training-resnet",
    hubId: "hub-ouarzazate",
    gpuHours: 192,
    cpuCoreHours: 768,
    memoryGbHours: 3072,
    storageGbMonths: 50,
    totalCost: 403.2,
    currency: "USD",
    status: "paid",
    periodStart: "2025-01-01T00:00:00Z",
    periodEnd: "2025-01-31T23:59:59Z",
  },
  {
    id: "bill-002",
    userId: "user-alice",
    workloadId: "wkld-llama-inference",
    hubId: "hub-dakhla",
    gpuHours: 720,
    cpuCoreHours: 1440,
    memoryGbHours: 5760,
    storageGbMonths: 200,
    totalCost: 1008,
    currency: "USD",
    status: "paid",
    periodStart: "2025-01-01T00:00:00Z",
    periodEnd: "2025-01-31T23:59:59Z",
  },
  {
    id: "bill-003",
    userId: "user-bob",
    workloadId: "wkld-finetune-mistral",
    hubId: "hub-benguerir",
    gpuHours: 336,
    cpuCoreHours: 1344,
    memoryGbHours: 5376,
    storageGbMonths: 100,
    totalCost: 789.6,
    currency: "USD",
    status: "open",
    periodStart: "2025-02-01T00:00:00Z",
    periodEnd: "2025-02-28T23:59:59Z",
  },
  {
    id: "bill-004",
    userId: "user-carol",
    workloadId: "wkld-rag-pipeline",
    hubId: "hub-tanger",
    gpuHours: 48,
    cpuCoreHours: 192,
    memoryGbHours: 768,
    storageGbMonths: 500,
    totalCost: 86.4,
    currency: "USD",
    status: "overdue",
    periodStart: "2024-12-01T00:00:00Z",
    periodEnd: "2024-12-31T23:59:59Z",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_ICONS: Record<string, string> = {
  paid: "✅",
  open: "🟡",
  closed: "🔵",
  overdue: "🔴",
};

function printRecords(records: SimulatedRecord[]): void {
  if (!records.length) {
    console.log("\n  No billing records found.");
    return;
  }

  console.log(
    `\n  ${"ID".padEnd(12)} | ${"Workload".padEnd(28)} | ${"Hub".padEnd(18)} | ` +
    `${"GPU hrs".padStart(8)} | ${"Total".padStart(10)} | ${"Currency".padEnd(8)} | Status`
  );
  console.log("  " + "-".repeat(110));

  for (const r of records) {
    const icon = STATUS_ICONS[r.status] || "⚪";
    console.log(
      `  ${r.id.padEnd(12)} | ${(r.workloadId || "N/A").padEnd(28)} | ` +
      `${(r.hubId || "N/A").padEnd(18)} | ` +
      `${r.gpuHours.toFixed(1).padStart(8)} | ` +
      `${r.totalCost.toFixed(2).padStart(10)} | ${r.currency.padEnd(8)} | ` +
      `${icon} ${r.status}`
    );
  }
}

interface CurrencySummary {
  total: number;
  byStatus: Record<string, number>;
  totalGpuHours: number;
  recordCount: number;
}

function computeSummary(records: SimulatedRecord[]): Record<string, CurrencySummary> {
  const summary: Record<string, CurrencySummary> = {};

  for (const r of records) {
    if (!summary[r.currency]) {
      summary[r.currency] = { total: 0, byStatus: {}, totalGpuHours: 0, recordCount: 0 };
    }
    const s = summary[r.currency];
    s.total += r.totalCost;
    s.totalGpuHours += r.gpuHours;
    s.recordCount += 1;
    s.byStatus[r.status] = (s.byStatus[r.status] || 0) + r.totalCost;
  }

  return summary;
}

function printSummary(summary: Record<string, CurrencySummary>): void {
  console.log("\n  📊 Spending Summary");
  console.log("  " + "=".repeat(50));

  for (const [currency, data] of Object.entries(summary)) {
    console.log(`\n  Currency: ${currency}`);
    console.log(`    Total spent:      ${data.total.toFixed(2).padStart(10)} ${currency}`);
    console.log(`    Total GPU hours:  ${data.totalGpuHours.toFixed(1).padStart(10)} hrs`);
    console.log(`    Record count:     ${data.recordCount.toString().padStart(10)}`);

    console.log("    By status:");
    for (const [status, amount] of Object.entries(data.byStatus)) {
      const icon = STATUS_ICONS[status] || "⚪";
      console.log(`      ${icon} ${status.padEnd(10)}: ${amount.toFixed(2).padStart(10)} ${currency}`);
    }

    const overdue = data.byStatus["overdue"] || 0;
    if (overdue > 0) {
      console.log(`\n    ⚠️  OVERDUE: ${overdue.toFixed(2)} ${currency} requires immediate attention!`);
    }
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const statusFilter = getArg(args, "--status", "") as ListBillingRecordsParams["status"] | "";

  console.log("=".repeat(60));
  console.log("HarchOS Billing History (TypeScript)");
  console.log("=".repeat(60));

  let records: SimulatedRecord[];

  // Try SDK, fall back to simulated data
  const apiKey = process.env.HARCHOS_API_KEY || "";
  if (apiKey) {
    try {
      const client = new HarchOSClient({ apiKey });
      const params: ListBillingRecordsParams = {};
      if (statusFilter) params.status = statusFilter;

      const sdkRecords = await client.pricing.listBillingRecords(params);
      records = sdkRecords.map((r) => ({
        id: r.id,
        userId: r.userId,
        workloadId: r.workloadId || "N/A",
        hubId: r.hubId || "N/A",
        gpuHours: r.gpuHours,
        cpuCoreHours: r.cpuCoreHours,
        memoryGbHours: r.memoryGbHours,
        storageGbMonths: r.storageGbMonths,
        totalCost: r.totalCost,
        currency: r.currency,
        status: r.status,
        periodStart: r.periodStart,
        periodEnd: r.periodEnd,
      }));
    } catch (err) {
      console.error(`[ERROR] SDK call failed: ${err}`);
      console.log("[WARN] Falling back to simulated data");
      records = getSimulatedRecords(statusFilter);
    }
  } else {
    records = getSimulatedRecords(statusFilter);
  }

  printRecords(records);

  if (records.length) {
    const summary = computeSummary(records);
    printSummary(summary);
  }

  console.log();
}

function getSimulatedRecords(statusFilter: string): SimulatedRecord[] {
  if (statusFilter) {
    return SIMULATED_RECORDS.filter((r) => r.status === statusFilter);
  }
  return SIMULATED_RECORDS;
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
