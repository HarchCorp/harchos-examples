# 03 — Pricing-Optimized Multi-Region Deployment

Deploy workloads to the most cost-effective hub across HarchOS regions.

## What it does

- Compares pricing across all eligible hubs and regions
- Enforces carbon intensity constraints
- Respects sovereignty requirements (data residency, compliance frameworks)
- Recommends the best-value hub with alternatives
- Suggests constraint relaxation when no hub matches

## Usage

### Python

```bash
# Basic optimization
python pricing_optimized.py --gpu-type H100 --gpu-count 8 --hours 168

# With carbon constraint
python pricing_optimized.py --carbon-max 100

# Sovereign-only hubs
python pricing_optimized.py --sovereign-only

# Specific tier
python pricing_optimized.py --tier enterprise --carbon-max 50
```

### TypeScript

```bash
# Basic optimization
npx ts-node pricing_optimized.ts --gpu-type H100 --gpu-count 8

# With carbon constraint
npx ts-node pricing_optimized.ts --carbon-max 100
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.regions.list()` | `GET /v1/regions` |
| Python | `client.pricing.estimate_cost()` | `POST /v1/pricing/estimate` |
| TypeScript | `client.regions.list()` | `GET /v1/regions` |
| TypeScript | `client.pricing.estimateCost()` | `POST /v1/pricing/estimate` |

## Best Practices

- **Always set a carbon max** — use `--carbon-max 100` for green deployments
- **Use `--sovereign-only`** for workloads with data residency requirements
- **Compare alternatives** — the cheapest hub isn't always the greenest
- **Consider tier requirements** — enterprise tier includes priority support and SLAs
