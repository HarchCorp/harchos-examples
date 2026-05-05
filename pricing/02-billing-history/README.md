# 02 — Billing History

Retrieve and analyze billing records from the HarchOS platform.

## What it does

- Lists billing records with status and date filters
- Computes spending summaries by currency and status
- Highlights overdue records with alerts
- Shows GPU hours consumed per billing period

## Usage

### Python

```bash
# Show all records
python billing_history.py

# Filter by status
python billing_history.py --status overdue

# Last 30 days only
python billing_history.py --last-30-days
```

### TypeScript

```bash
# Show all records
npx ts-node billing_history.ts

# Filter by status
npx ts-node billing_history.ts --status overdue
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.pricing.list_billing_records()` | `GET /v1/pricing/billing/records` |
| TypeScript | `client.pricing.listBillingRecords()` | `GET /v1/pricing/billing/records` |

## Best Practices

- **Monitor overdue bills** — use `--status overdue` in automated checks
- **Track GPU hours** — compare GPU-hours against workload estimates
- **Multi-currency awareness** — HarchOS supports both USD and MAD billing
