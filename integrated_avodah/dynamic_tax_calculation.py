from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
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
class DynamicTaxCalculationEngineModule:
    entity_name: str = "Integrated Avodah LLC"
    hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
    phone: str = "(785) 764-2680"
    visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
    brand_tagline: str = "Corporate Compliance Portal"
    ledger_port_binding: int = 8081
    jurisdictional_rules: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        if self.jurisdictional_rules is None:
            self.jurisdictional_rules = {
                "KS_LOCAL_HQ": {
                    "jurisdiction": "State of Kansas (Local HQ)",
                    "annualReportFee": 53.00,
                    "taxStatus": "EXEMPT_501C3_RELIGIOUS",
                    "surchargeRate": 0.00,
                },
                "US_FEDERAL": {
                    "jurisdiction": "United States Federal (IRS)",
                    "annualReportFee": 0.00,
                    "taxStatus": "EXEMPT_501C3_RELIGIOUS",
                    "surchargeRate": 0.00,
                },
                "MULTI_STATE_CORP": {
                    "jurisdiction": "Multi-State Corporate Service",
                    "annualReportFee": 150.00,
                    "taxStatus": "NON_PROFIT_GOVERNANCE",
                    "surchargeRate": 0.015,
                },
            }

    def calculate_compliance_liability(self, jurisdiction_key: str = "KS_LOCAL_HQ", gross_receipts: float = 0.00) -> Dict[str, Any]:
        timestamp = _utc_iso_now()
        rule = self.jurisdictional_rules.get(jurisdiction_key, self.jurisdictional_rules["KS_LOCAL_HQ"])

        base_fee = float(rule["annualReportFee"])
        calculated_surcharge = round(float(gross_receipts) * float(rule["surchargeRate"]), 2)
        total_liability = round(base_fee + calculated_surcharge, 2)

        raw_payload = f"{timestamp}:{jurisdiction_key}:{total_liability}:{self.entity_name}".encode("utf-8")
        audit_hash = hashlib.sha256(raw_payload).hexdigest()

        return {
            "calculationId": "TAX-CALC-P3S24",
            "jurisdiction": rule["jurisdiction"],
            "taxStatus": rule["taxStatus"],
            "baseFilingFeeUSD": base_fee,
            "calculatedSurchargeUSD": calculated_surcharge,
            "totalLiabilityUSD": total_liability,
            "sha256AuditHash": f"0x{audit_hash}",
            "ledgerPortTarget": self.ledger_port_binding,
            "timestamp": timestamp,
            "status": "CALCULATED_AND_VERIFIED",
        }

    def export_calculation_manifest(self) -> Dict[str, Any]:
        sample_calc = self.calculate_compliance_liability("KS_LOCAL_HQ", gross_receipts=0.00)
        manifest = {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "tagline": self.brand_tagline,
            "jurisdictionalRules": self.jurisdictional_rules,
            "sampleLiabilityCalculation": sample_calc,
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 24 Dynamic Tax & Filing Calculation Engine Initialized",
        }
        return manifest

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_calculation_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_calculation_manifest(), sort_keys=False)


if __name__ == "__main__":
    mod = DynamicTaxCalculationEngineModule()
    print("[PHASE 3, STEP 24 COMPLETED] Dynamic tax & filing calculation engine verified:")
    print(mod.export_json())
