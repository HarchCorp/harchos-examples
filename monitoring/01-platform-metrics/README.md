# 01 — Platform Metrics

Display real-time HarchOS platform-wide metrics.

## What it does

- Shows GPU infrastructure stats (total, available, utilization)
- Displays workload statistics
- Reports energy consumption and renewable share
- Tracks carbon intensity and CO2 savings
- Categorizes utilization health (low → critical)
- Supports `--watch` for live monitoring

## Usage

### Python

```bash
# One-time metrics
python platform_metrics.py

# Live monitoring (refresh every 30s)
python platform_metrics.py --watch

# Custom refresh interval
python platform_metrics.py --watch --interval 60

# Raw JSON output
python platform_metrics.py --json
```

### TypeScript

```bash
# One-time metrics
npx ts-node platform_metrics.ts

# Live monitoring
npx ts-node platform_metrics.ts --watch
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |
| TypeScript | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |

## Key Metrics

| Metric | Description | Healthy Range |
|--------|-------------|---------------|
| `gpu_utilization_percent` | Average GPU utilization | 50-85% |
| `avg_renewable_percentage` | Renewable energy share | >80% |
| `avg_carbon_intensity` | gCO2/kWh average | <100 |
| `avg_pue` | Power Usage Effectiveness | <1.2 |
