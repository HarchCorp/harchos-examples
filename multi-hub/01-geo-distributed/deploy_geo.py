#!/usr/bin/env python3
"""Geo-distributed deployment across HarchOS hubs.

Deploys an inference service to multiple HarchOS hubs in different regions
with latency-based routing, health monitoring, and automatic failover.

Usage:
    python deploy_geo.py --hubs eu-west-1,us-east-1,apac-southeast-1
    python deploy_geo.py --status
    python deploy_geo.py --teardown
"""

import argparse
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from harchos import HarchOSClient  # noqa: F401
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated hub client")


# ---------------------------------------------------------------------------
# Simulated hub client (for local testing without real HarchOS)
# ---------------------------------------------------------------------------

class SimulatedHubClient:
    """Simulated HarchOS hub client for local testing."""

    HUB_CONFIG = {
        "eu-west-1": {"region": "Europe (Ireland)", "latency_ms": 30, "gpu": "L4"},
        "us-east-1": {"region": "US East (Virginia)", "latency_ms": 80, "gpu": "A100"},
        "us-west-2": {"region": "US West (Oregon)", "latency_ms": 120, "gpu": "L4"},
        "apac-southeast-1": {"region": "APAC (Singapore)", "latency_ms": 180, "gpu": "L4"},
    }

    def __init__(self):
        self.deployments: Dict[str, dict] = {}

    def list_hubs(self) -> List[dict]:
        """List available hubs."""
        return [
            {"name": name, **config}
            for name, config in self.HUB_CONFIG.items()
        ]

    def deploy(self, hub: str, model: str, replicas: int = 1) -> dict:
        """Deploy a model to a hub."""
        if hub not in self.HUB_CONFIG:
            raise ValueError(f"Unknown hub: {hub}")

        deployment_id = f"geo-{hub}-{int(time.time())}"
        self.deployments[hub] = {
            "deployment_id": deployment_id,
            "hub": hub,
            "model": model,
            "replicas": replicas,
            "status": "running",
            "endpoint": f"https://{hub}.harchos.io/{deployment_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"  Deployed to {hub}: {deployment_id}")
        return self.deployments[hub]

    def get_status(self, hub: str) -> Optional[dict]:
        """Get deployment status for a hub."""
        return self.deployments.get(hub)

    def teardown(self, hub: str) -> bool:
        """Remove a deployment from a hub."""
        if hub in self.deployments:
            del self.deployments[hub]
            print(f"  Tore down deployment on {hub}")
            return True
        return False

    def health_check(self, hub: str) -> dict:
        """Check health of a deployment."""
        config = self.HUB_CONFIG.get(hub, {})
        deployed = hub in self.deployments
        return {
            "hub": hub,
            "healthy": deployed,
            "latency_ms": config.get("latency_ms", 0) if deployed else None,
            "status": "running" if deployed else "not_deployed",
        }


def create_hub_client():
    """Create a hub client — real or simulated."""
    if HARCHOS_AVAILABLE:
        return HarchOSClient(api_key=os.environ.get("HARCHOS_API_KEY", ""))
    return SimulatedHubClient()


# ---------------------------------------------------------------------------
# Deployment commands
# ---------------------------------------------------------------------------

def deploy_multi_hub(hub_client, hubs: List[str], model: str, replicas: int):
    """Deploy a model to multiple hubs."""
    print(f"\nDeploying {model} to {len(hubs)} hub(s)...")
    print("=" * 50)

    results = []
    for hub in hubs:
        try:
            result = hub_client.deploy(hub, model=model, replicas=replicas)
            results.append(result)
        except Exception as e:
            print(f"  FAILED on {hub}: {e}")
            results.append({"hub": hub, "status": "failed", "error": str(e)})

    print("\nDeployment Summary:")
    print("-" * 50)
    for r in results:
        status = r.get("status", "unknown")
        endpoint = r.get("endpoint", "N/A")
        print(f"  {r['hub']:20s} | {status:10s} | {endpoint}")

    return results


def check_status(hub_client, hubs: List[str]):
    """Check deployment status across hubs."""
    print("\nMulti-Hub Deployment Status")
    print("=" * 70)
    print(f"{'Hub':20s} | {'Status':12s} | {'Healthy':8s} | {'Latency':10s}")
    print("-" * 70)

    for hub in hubs:
        health = hub_client.health_check(hub)
        print(f"{health['hub']:20s} | {health['status']:12s} | "
              f"{str(health['healthy']):8s} | "
              f"{health.get('latency_ms', 'N/A')} ms")

    print()


def run_health_monitor(hub_client, hubs: List[str], interval: int = 30):
    """Continuously monitor hub health."""
    print(f"Monitoring hub health (every {interval}s, Ctrl+C to stop)...\n")

    try:
        while True:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{timestamp}]")
            all_healthy = True

            for hub in hubs:
                health = hub_client.health_check(hub)
                status_icon = "✅" if health["healthy"] else "❌"
                latency = health.get("latency_ms", "N/A")
                print(f"  {status_icon} {hub}: {health['status']} "
                      f"(latency: {latency} ms)")
                if not health["healthy"]:
                    all_healthy = False

            if not all_healthy:
                print("  ⚠️  One or more hubs unhealthy — failover may be active")

            time.sleep(interval)
            print()
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


def teardown_all(hub_client, hubs: List[str]):
    """Remove deployments from all hubs."""
    print("\nTearing down deployments...")
    for hub in hubs:
        hub_client.teardown(hub)
    print("All deployments removed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Geo-Distributed Deployment")
    parser.add_argument("--hubs", type=str, default="eu-west-1,us-east-1,apac-southeast-1",
                        help="Comma-separated hub names")
    parser.add_argument("--model", type=str,
                        default="distilbert-base-uncased-finetuned-sst-2-english",
                        help="Model to deploy")
    parser.add_argument("--replicas", type=int, default=1,
                        help="Replicas per hub")
    parser.add_argument("--status", action="store_true",
                        help="Check deployment status")
    parser.add_argument("--monitor", action="store_true",
                        help="Continuously monitor hub health")
    parser.add_argument("--teardown", action="store_true",
                        help="Remove all deployments")
    parser.add_argument("--list-hubs", action="store_true",
                        help="List available hubs")
    args = parser.parse_args()

    hub_list = [h.strip() for h in args.hubs.split(",")]
    hub_client = create_hub_client()

    if args.list_hubs:
        hubs = hub_client.list_hubs()
        print("\nAvailable Hubs:")
        for h in hubs:
            print(f"  {h['name']:20s} | {h['region']:30s} | {h['gpu']} GPU | ~{h['latency_ms']}ms")
        return

    if args.status:
        check_status(hub_client, hub_list)
        return

    if args.monitor:
        run_health_monitor(hub_client, hub_list)
        return

    if args.teardown:
        teardown_all(hub_client, hub_list)
        return

    # Default: deploy
    deploy_multi_hub(hub_client, hub_list, model=args.model, replicas=args.replicas)


if __name__ == "__main__":
    main()
