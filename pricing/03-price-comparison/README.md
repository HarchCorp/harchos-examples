# 03 — Price Comparison

Compare GPU pricing across HarchOS hubs, regions, and tiers.

## What it does

- Compares pricing across all GPU types (H100, A100, L40S)
- Ranks plans by cost per GPU-hour
- Optionally adjusts for carbon cost with `--include-carbon`
- Recommends the best-value plan

## Usage

### Python

```bash
# Compare all plans
python price_comparison.py

# Filter by GPU type
python price_comparison.py --gpu-type H100

# Carbon-adjusted comparison
python price_comparison.py --include-carbon

# Compare tiers
python price_comparison.py --compare-tiers --gpu-type H100
```

### TypeScript

```bash
# Compare all plans
npx ts-node price_comparison.ts

# Carbon-adjusted comparison
npx ts-node price_comparison.ts --include-carbon
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.pricing.list_plans()` | `GET /v1/pricing/plans` |
| TypeScript | `client.pricing.listPlans()` | `GET /v1/pricing/plans` |

## Carbon-Adjusted Pricing

When `--include-carbon` is used, the effective cost per GPU-hour includes:

- **Direct cost**: Plan's price per GPU-hour
- **Carbon cost**: Estimated CO2 emissions × $50/tonne social cost of carbon
- **Formula**: `effective_cost = direct_cost + (0.3 kWh × carbon_intensity / 1000 kg) × $0.05/kg`

This reveals that greener hubs (Ouarzazate at 18 gCO2/kWh) are often more cost-effective than cheaper-but-dirtier alternatives when environmental externalities are factored in.
