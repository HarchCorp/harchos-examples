# 03 — Carbon Dashboard

Build a comprehensive carbon metrics dashboard for HarchOS.

## What it does

- Shows platform-wide carbon intensity and renewable energy share
- Computes carbon savings vs industry average (~450 gCO2/kWh)
- Breaks down carbon metrics per hub (Ouarzazate, Dakhla, Benguerir, Tanger, Casablanca)
- Detects green windows for optimal scheduling
- Tracks carbon budget compliance
- Shows carbon equivalents (trees, cars)

## Usage

### Python

```bash
# Basic dashboard
python carbon_dashboard.py

# Detailed analysis with equivalents
python carbon_dashboard.py --detailed

# Carbon budget check
python carbon_dashboard.py --carbon-budget 5000

# JSON output
python carbon_dashboard.py --json
```

### TypeScript

```bash
# Basic dashboard
npx ts-node carbon_dashboard.ts

# Detailed analysis
npx ts-node carbon_dashboard.ts --detailed

# Carbon budget check
npx ts-node carbon_dashboard.ts --carbon-budget 5000
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |
| Python | `client.carbon.get_dashboard()` | `GET /v1/carbon/dashboard` |
| TypeScript | `client.monitoring.metrics()` | `GET /v1/monitoring/metrics` |

## Carbon Intensity Scale

| Range | Rating | Icon | Meaning |
|-------|--------|------|---------|
| ≤ 100 gCO2/kWh | GREEN | 🟢 | Optimal for scheduling |
| 100-200 gCO2/kWh | ACCEPTABLE | 🟡 | Schedule if no green hub available |
| > 200 gCO2/kWh | AVOID | 🔴 | Defer workloads if possible |

## Key Insight

HarchOS's average carbon intensity of **47 gCO2/kWh** is **89.6% lower** than the global data center industry average of 450 gCO2/kWh, thanks to Morocco's exceptional solar and wind resources.
