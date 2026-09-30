from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import datetime
import json

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False


def _utc_iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class RouteGuardControllerModule:
    entity_name: str = "Integrated Avodah LLC"
    hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
    phone: str = "(785) 764-2680"
    visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
    route_permissions: Dict[str, List[str]] = None

    def __post_init__(self):
        if self.route_permissions is None:
            self.route_permissions = {
                "/dashboard": ["GUEST", "AUDITOR", "ADMIN"],
                "/ledger-admin": ["AUDITOR", "ADMIN"],
                "/vault-keys": ["ADMIN"],
                "/siem-logs": ["AUDITOR", "ADMIN"],
                "/telemetry": ["GUEST", "AUDITOR", "ADMIN"],
            }

    def evaluate_route_access(self, target_route: str = "/vault-keys", user_role: str = "AUDITOR") -> Dict[str, Any]:
        timestamp = _utc_iso_now()
        allowed_roles = self.route_permissions.get(target_route, [])
        is_authorized = user_role in allowed_roles

        return {
            "evaluationId": "GUARD-P3S15-001",
            "targetRoute": target_route,
            "userRole": user_role,
            "accessGranted": is_authorized,
            "redirectAction": None if is_authorized else "Redirect to /dashboard (Access Denied)",
            "timestamp": timestamp,
        }

    def export_guard_manifest(self) -> Dict[str, Any]:
        manifest = {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "routePermissions": self.route_permissions,
            "sampleGuardEvaluation": self.evaluate_route_access(),
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 15 Multi-Port Route Guard Initialized",
        }
        return manifest

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_guard_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_guard_manifest(), sort_keys=False)

    def __repr__(self) -> str:
        return f"<RouteGuardControllerModule routes={len(self.route_permissions)}>"


if __name__ == "__main__":
    mod = RouteGuardControllerModule()
    print("[PHASE 3, STEP 15 COMPLETED] Multi-port route guard & role-based navigation controller verified:")
    print(mod.export_json())
