# 02 — Health Check

Detailed health check and status monitoring for the HarchOS platform.

## What it does

- Checks API server health status (healthy/degraded/unhealthy)
- Verifies database connectivity
- Reports uptime in human-readable format
- Shows active connections and endpoint count
- Displays sovereignty compliance requirements
- Supports exit codes for alerting integration

## Usage

### Python

```bash
# One-time health check
python health_check.py

# Continuous monitoring
python health_check.py --watch --interval 60

# Exit code for alerting (0=healthy, 1=degraded, 2=unhealthy)
python health_check.py --exit-code

# JSON output for programmatic use
python health_check.py --json
```

### TypeScript

```bash
# One-time health check
npx ts-node health_check.ts

# Continuous monitoring
npx ts-node health_check.ts --watch

# Exit code for alerting
npx ts-node health_check.ts --exit-code
```

## SDK Methods Used

| Language | Method | Endpoint |
|----------|--------|----------|
| Python | `client.monitoring.detailed_health()` | `GET /v1/monitoring/health/detailed` |
| TypeScript | `client.monitoring.detailedHealth()` | `GET /v1/monitoring/health/detailed` |

## Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | `healthy` | All systems operational |
| 1 | `degraded` | Partial issues, monitoring recommended |
| 2 | `unhealthy` | Critical issues, immediate action needed |

## Alerting Integration

Use with cron or monitoring tools:

```bash
# Cron-based check every 5 minutes
*/5 * * * * python /path/to/health_check.py --exit-code || send-alert.sh
```
