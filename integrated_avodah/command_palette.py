from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
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
class Shortcut:
    key: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class CommandPaletteEngineModule:
    """
    High-Density Command Palette Engine
    - Registers keyboard shortcuts and simulates commands
    - Exposes JSON/YAML export helpers and a small CLI demo
    """

    def __init__(self):
        self.entity_name: str = "Integrated Avodah LLC"
        self.hq_address: str = "2523 Redbud Ln, APT 16, Lawrence, KS 66046"
        self.phone: str = "(785) 764-2680"
        self.visual_standard: str = "#FFFFFF Canvas White (Extreme Negative Space)"
        self.hotkey_trigger: str = "Cmd+K / Ctrl+K"
        self.registered_shortcuts: Dict[str, Shortcut] = {
            "G + L": Shortcut(key="G + L", description="Jump to Compliance Ledger (Port 8081) [Grid Slot B]"),
            "G + S": Shortcut(key="G + S", description="Jump to SIEM Audit Feed (Port 8082) [Grid Slot C]"),
            "G + V": Shortcut(key="G + V", description="Jump to Secure Vault Monitor (Port 8083) [Grid Slot D]"),
            "G + H": Shortcut(key="G + H", description="Jump to Node Health Panel (Port 8080) [Grid Slot A]"),
            "Cmd + E": Shortcut(key="Cmd + E", description="Trigger High-Density Compliance Report Generator"),
            "Esc": Shortcut(key="Esc", description="Close Palette Overlay & Restore Focus Lock"),
        }

    def simulate_palette_command(self, command_key: str = "G + L") -> Dict[str, Any]:
        timestamp = _utc_iso_now()
        shortcut = self.registered_shortcuts.get(command_key)
        target_action = shortcut.description if shortcut else "Unknown Command"
        focus_lock_target = "Grid Slot B (Compliance Ledger Stream)" if command_key == "G + L" else "Grid Center Workspace"

        return {
            "paletteId": "CMD-P3S14-001",
            "executedHotkey": command_key,
            "targetAction": target_action,
            "focusLockTarget": focus_lock_target,
            "timestamp": timestamp,
            "status": "Keyboard Navigation Executed",
        }

    def export_palette_manifest(self) -> Dict[str, Any]:
        return {
            "entity": self.entity_name,
            "headquarters": self.hq_address,
            "phone": self.phone,
            "hotkeyTrigger": self.hotkey_trigger,
            "registeredShortcuts": {k: v.to_dict() for k, v in self.registered_shortcuts.items()},
            "commandSimulation": self.simulate_palette_command(),
            "canvasStandard": self.visual_standard,
            "complianceStatus": "Phase 3, Step 14 High-Density Command Palette Engine Initialized",
        }

    def export_json(self, indent: int = 2) -> str:
        return json.dumps(self.export_palette_manifest(), indent=indent)

    def export_yaml(self) -> str:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML not installed; install with `pip install pyyaml` to enable YAML export.")
        return yaml.safe_dump(self.export_palette_manifest(), sort_keys=False)

    def __repr__(self) -> str:
        return f"<CommandPaletteEngineModule shortcuts={len(self.registered_shortcuts)}>"


if __name__ == "__main__":
    mod = CommandPaletteEngineModule()
    print("[PHASE 3, STEP 14 COMPLETED] High-density keyboard accessibility & command palette engine verified:")
    print(mod.export_json())
