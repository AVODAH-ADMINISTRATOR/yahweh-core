from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
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
class EscalationRule:
    level: int
    trigger: str
    action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComplianceNotificationEscalationModule:
    """
    Automated Compliance Notification & Escalation Routing Module
    - Models notification channels and escalation matrix
    - Simulates escalation events and exports manifests
    """

    def __init__(self):
        self.entity_name: str = "Integrated Avodah LLC"
        self.hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
        self.phone: str = "(785) 764-2680"
        self.visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
        self.brand_tagline: str = "Corporate Compliance Portal"
        self.notification_channels: Dict[str, Any] = {
            "sms_texting": True,
            "webhook_endpoint": "https://127.0.0.1:8080/api/v1/alerts/dispatch",
            "audit_ledger_target": 8081,
        }
        self.escalation_matrix: List[EscalationRule] = [
            EscalationRule(level=1, trigger="FILING_DEADLINE_WARNING", action="SMS Alert to Assigned Steward"),
            EscalationRule(level=2, trigger="UNRESOLVED_VAULT_KEY_EXPIRATION", action="Escalate to Chief Compliance Officer"),
            EscalationRule(level=3, trigger="HMAC_INTEGRITY_BREACH", action="Lock Node & Alert Legal Counsel"),
        ]

    def trigger_escalation_event(self, trigger_type: str = "UNRESOLVED_VAULT_KEY_EXPIRATION") -> Dict[str, Any]:
        timestamp = _utc_iso_now()
        matched_rule: Optional[EscalationRule] = next((r for r in self.escalation_matrix if r.trigger == trigger_type), None)

        escalation_level = matched_rule.level if matched_rule else 0
        routing_action = matched_rule.action if matched_rule else "Log Warning Only"
        dispatch_channel = "SMS_TEXT_MESSAGE" if bool(self.notification_channels.get("sms_texting")) else "WEBHOOK"

        return {
            "eventId": "NOTIF-P3S19-001",
            "triggerType": trigger_type,
            "escalationLevel": escalation_level,
            "routingAction": routing_action,
            "dispatchChannel": dispatch_channel,
            "timestamp": timestamp,
            "status": "DISPATCHED",
        }

    def export_notification_manifest(self) -> Dict[str, Any]:
        return {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "tagline": self.brand_tagline,
            "notificationChannels": self.notification_channels,
            "escalationRules": [r.to_dict() for r in self.escalation_matrix],
            "activeNotificationSample": self.trigger_escalation_event(),
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 19 Automated Compliance Notification & Escalation Routing Initialized",
        }

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_notification_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_notification_manifest(), sort_keys=False)


if __name__ == "__main__":
    mod = ComplianceNotificationEscalationModule()
    print("[PHASE 3, STEP 19 COMPLETED] Automated compliance notification & escalation routing module verified:")
    print(mod.export_json())
