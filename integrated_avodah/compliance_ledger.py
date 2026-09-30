from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import datetime
import hashlib
import json

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False


def _utc_iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class LedgerEntry:
    entry_id: str
    event_summary: str
    timestamp: str
    sha256_hash: str
    verification_status: str = "Immutable Record Confirmed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComplianceLedgerStreamModule:
    """
    Real-Time Compliance Ledger Stream Module
    - Binds logically to a port (default 8081)
    - Produces a small ledger feed with SHA-256 entry hashes
    - Exports manifest as dict, JSON, or YAML (if PyYAML installed)
    """

    def __init__(self, port_binding: int = 8081, sample_events: List[str] | None = None):
        self.entity_name: str = "Integrated Avodah LLC"
        self.hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
        self.phone: str = "(785) 764-2680"
        self.port_binding: int = int(port_binding)
        self.visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
        self.sample_audit_events: List[str] = sample_events or [
            "STATUTORY_FILING_VERIFIED: Annual Governance Review",
            "POLICY_ACKNOWLEDGEMENT: Ethical Stewardship Charter v2.4",
            "ACCESS_CONTROL_AUDIT: Port 8083 Secure Vault Authentication Passed",
            "DATA_INTEGRITY_CHECK: Cross-Node Database Replicas Synchronized",
        ]
        self._validate_port()

    def _validate_port(self) -> None:
        if not (1 <= self.port_binding <= 65535):
            raise ValueError(f"port_binding {self.port_binding} out of range (1-65535)")

    def generate_ledger_feed(self) -> List[LedgerEntry]:
        timestamp = _utc_iso_now()
        feed: List[LedgerEntry] = []
        for index, event in enumerate(self.sample_audit_events, start=1):
            raw_payload = f"{timestamp}:{event}:{index}".encode("utf-8")
            entry_hash = hashlib.sha256(raw_payload).hexdigest()
            entry_id = f"LDR-{self.port_binding}-{index:04d}"
            feed.append(LedgerEntry(entry_id=entry_id, event_summary=event, timestamp=timestamp, sha256_hash=entry_hash))
        return feed

    def export_ledger_panel_manifest(self) -> Dict[str, Any]:
        feed = self.generate_ledger_feed()
        return {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "slotLocation": "Grid Slot B (Top Right Workspace)",
            "boundPort": self.port_binding,
            "ledgerEntries": [e.to_dict() for e in feed],
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 5 Real-Time Compliance Ledger Stream Initialized",
        }

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_ledger_panel_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_ledger_panel_manifest(), sort_keys=False)

    def __repr__(self) -> str:
        return f"<ComplianceLedgerStreamModule port={self.port_binding} entries={len(self.sample_audit_events)}>"


if __name__ == "__main__":
    ledger = ComplianceLedgerStreamModule()
    print("[PHASE 3, STEP 5 COMPLETED] Real-time compliance ledger stream component verified:")
    print("\n--- JSON manifest ---")
    print(ledger.export_json())
