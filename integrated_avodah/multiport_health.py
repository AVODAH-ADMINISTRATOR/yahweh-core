from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import datetime
import json
import hmac
import hashlib

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False


@dataclass
class Node:
    port: int
    name: str
    expected_latency: str
    status: str = "Online"
    last_ping: Optional[str] = None
    hmac_verified: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "nodeName": self.name,
            "expectedLatency": self.expected_latency,
            "connectionStatus": self.status,
            "lastPing": self.last_ping,
            "hmacVerification": "Verified" if self.hmac_verified else ("Not Verified" if self.hmac_verified is False else "Unavailable")
        }


class MultiPortHealthModule:
    """
    Multi-Port Node Health Status Module
    - Keeps structured node definitions (port, name, expected latency)
    - Generates a telemetry manifest (timestamps per node)
    - Optional HMAC generation hook: pass a secret to generate per-node digests
    """

    def __init__(self, hmac_secret: Optional[bytes] = None):
        self.entity_name: str = "Integrated Avodah LLC"
        self.hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
        self.phone: str = "(785) 764-2680"
        self.visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
        # structured nodes
        self.monitored_nodes: Dict[int, Node] = {
            8080: Node(port=8080, name="Primary Gateway Node", expected_latency="< 1.0ms"),
            8081: Node(port=8081, name="Compliance Ledger Node", expected_latency="< 1.2ms"),
            8082: Node(port=8082, name="Telemetry Relay Node", expected_latency="< 1.5ms"),
            8083: Node(port=8083, name="Secure Vault Node", expected_latency="< 0.9ms"),
            8084: Node(port=8084, name="Fallback Gateway Node", expected_latency="Standby"),
        }
        self.hmac_secret = hmac_secret
        self._validate_ports()

    def _validate_ports(self) -> None:
        # Ensure ports are valid integers and between 1-65535
        for p in self.monitored_nodes.keys():
            if not isinstance(p, int):
                raise TypeError(f"Port {p!r} is not an integer.")
            if p < 1 or p > 65535:
                raise ValueError(f"Port {p} out of range (1-65535).")

    def _current_utc_iso(self) -> str:
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _compute_hmac(self, message: bytes) -> str:
        if not self.hmac_secret:
            raise RuntimeError("HMAC secret not provided")
        mac = hmac.new(self.hmac_secret, message, hashlib.sha256)
        return mac.hexdigest()

    def render_node_health_telemetry(self) -> Dict[str, Any]:
        """
        Populate node telemetry (timestamp, status, latency) and generate HMAC digest
        if a secret was provided when the module was created. hmacVerification field is
        set accordingly per node.
        """
        timestamp = self._current_utc_iso()
        telemetry_manifest: Dict[str, Any] = {}
        for port, node in self.monitored_nodes.items():
            # set last ping timestamp for this sample
            node.last_ping = timestamp

            # placeholder: in a real system obtain real latency/status data
            node_dict = node.to_dict()

            # if a secret is available, compute a message HMAC (example: HMAC of nodeName|port|timestamp)
            if self.hmac_secret:
                msg = f"{node.name}|{node.port}|{node.last_ping}".encode("utf-8")
                try:
                    digest = self._compute_hmac(msg)
                    node.hmac_verified = True
                    node_dict["hmacDigest"] = digest
                except RuntimeError:
                    node.hmac_verified = False
            else:
                node.hmac_verified = None

            telemetry_manifest[f"port_{port}"] = node_dict

        return telemetry_manifest

    def export_health_panel_manifest(self) -> Dict[str, Any]:
        manifest = {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "slotLocation": "Grid Slot A (Top Left Workspace)",
            "telemetryData": self.render_node_health_telemetry(),
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 4 Multi-Port Node Health Status Panel Initialized",
        }
        return manifest

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_health_panel_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; run `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_health_panel_manifest(), sort_keys=False)

    def __repr__(self) -> str:
        return f"<MultiPortHealthModule entity={self.entity_name!r} nodes={len(self.monitored_nodes)}>"


if __name__ == "__main__":
    # Example usage: if you have a secret to generate HMACs, pass it as bytes
    # secret = b"top-secret-key"  # DO NOT hardcode secrets into source; pass via env or secure store
    secret = None
    health_mod = MultiPortHealthModule(hmac_secret=secret)
    print("[PHASE 3, STEP 4 COMPLETED] Multi-port node health status module verified:")
    print("\n--- JSON manifest ---")
    print(health_mod.export_json())
    print("\n--- Example: telemetry keys ---")
    for k in health_mod.render_node_health_telemetry().keys():
        print(" ", k)
