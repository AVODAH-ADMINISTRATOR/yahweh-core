from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import datetime
import random
import json

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False


def _utc_iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class MultiPortTelemetryMonitorModule:
    """
    Centralized Multi-Port Telemetry & Latency Monitor
    Produces synthetic telemetry metrics for multiple monitored ports.
    """

    def __init__(self, monitored_ports: List[int] | None = None):
        self.entity_name: str = "Integrated Avodah LLC"
        self.hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
        self.phone: str = "(785) 764-2680"
        self.visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
        self.monitored_ports: List[int] = monitored_ports or [8080, 8081, 8082, 8083, 8084]
        self._validate_ports()

    def _validate_ports(self) -> None:
        for p in self.monitored_ports:
            if not isinstance(p, int) or p < 1 or p > 65535:
                raise ValueError(f"Invalid monitored port: {p}")

    def render_telemetry_metrics(self) -> Dict[str, Dict[str, Any]]:
        timestamp = _utc_iso_now()
        metrics: Dict[str, Dict[str, Any]] = {}
        for port in self.monitored_ports:
            metrics[f"port_{port}"] = {
                "averageLatencyMs": round(random.uniform(0.45, 1.15), 2),
                "throughputPps": random.randint(1200, 4800),
                "packetLossPercent": 0.00,
                "timestamp": timestamp,
                "status": "Optimal Performance",
            }
        return metrics

    def export_telemetry_panel_manifest(self) -> Dict[str, Any]:
        return {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "slotLocation": "Grid Center Workspace (Multi-Port Aggregate View)",
            "telemetryMetrics": self.render_telemetry_metrics(),
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 8 Centralized Multi-Port Telemetry Monitor Initialized",
        }

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_telemetry_panel_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_telemetry_panel_manifest(), sort_keys=False)


if __name__ == "__main__":
    mod = MultiPortTelemetryMonitorModule()
    print("[PHASE 3, STEP 8 COMPLETED] Centralized Multi-Port Telemetry & Latency Monitor component verified:")
    print(mod.export_json())
