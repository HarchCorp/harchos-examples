# 01 — Cost Estimator

Calculate GPU deployment costs before committing resources.

## What it does

- Estimates costs for different GPU types (H100, A100, L40S) and regions
- Shows detailed cost breakdown (GPU, CPU, memory, storage, network, tax)
- Compares costs across GPU types with `--compare`
- Validates estimates against a budget with `--budget`

## Usage

### Python

```bash
# Basic estimate
python cost_estimate.py --gpu-type H100 --gpu-count 4 --hours 24

# Compare all GPU types
python cost_estimate.py --compare --gpu-count 8 --hours 168

# Budget validation
python cost_estimate.py --gpu-type A100 --gpu-count 8 --hours 48 --budget 500
```

### TypeScript

```bash
# Basic estimate
npx ts-node cost_estimate.ts --gpu-type H100 --gpu-count 4 --hours 24

# Compare all GPU types
npx ts-node cost_estimate.ts --compare --gpu-count 8 --hours 168
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.pricing.estimate_cost()` | `POST /v1/pricing/estimate` |
| TypeScript | `client.pricing.estimateCost()` | `POST /v1/pricing/estimate` |

## Best Practices

- **Always estimate before deploying** — avoid budget overruns
- **Use `--compare`** to find the most cost-effective GPU type for your workload
- **Consider carbon impact** — greener hubs (Ouarzazate, Dakhla) are often competitively priced
- **Factor in VAT** — Morocco applies 20% VAT on compute services
