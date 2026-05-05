# 04 — Cross-Region Monitoring Dashboard

Unified monitoring dashboard across all HarchOS regions.

## What it does

- Displays platform health (API status, database, uptime)
- Shows platform-wide metrics (GPUs, utilization, carbon, CO2 savings)
- Lists all regions with compliance frameworks
- Breaks down hub details with carbon intensity color coding
- Computes and displays alerts for utilization and carbon thresholds
- Supports `--watch` for real-time monitoring

## Usage

### Python

```bash
# One-time dashboard
python monitoring_dashboard.py

# Live monitoring
python monitoring_dashboard.py --watch --interval 60

# JSON output
python monitoring_dashboard.py --json
```

### TypeScript

```bash
# One-time dashboard
npx ts-node monitoring_dashboard.ts

# Live monitoring
npx ts-node monitoring_dashboard.ts --watch
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.monitoring.detailed_health()` | `GET /v1/monitoring/health/detailed` |
| Python | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |
| Python | `client.regions.list()` | `GET /v1/regions` |
| TypeScript | `client.monitoring.detailedHealth()` | `GET /v1/monitoring/health/detailed` |
| TypeScript | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| GPU Utilization | ≥ 85% | ≥ 95% |
| Carbon Intensity | ≥ 200 gCO2/kWh | ≥ 400 gCO2/kWh |
