"""Virtualized compatibility shell.

Android-style PC function and a Windows 10 shell are modeled as fluid
adapters inside Council OS. Host hardware stays decoupled: remnants are
not restored and the host is not wiped. Customization happens in the
virtual workspace, not on the Dell/Android/Windows installation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

FORBIDDEN_HOST_ACTIONS = frozenset(
    {
        "wipe_host",
        "restore_windows_remnants",
        "install_android_on_host",
        "format_disk",
        "replace_host_bootloader",
    }
)

ADAPTERS: FrozenSet[str] = frozenset(
    {
        "android_pc_dell",
        "windows10_shell",
        "linux_container",
        "api_surface",
        "ide_workspace",
    }
)

# Capability layers: computing expanded from manual ones-and-zeros labor
# to high-capacity storage, sharing, and inventor customization — still
# subordinate to charter. Not a claim that the machine matches omnipotence.
COMPUTING_EPOCHS: Tuple[Dict[str, str], ...] = (
    {"id": "manual_labor", "era": "pre-electronic", "mode": "hand computation"},
    {"id": "ones_and_zeros", "era": "electronic dawn", "mode": "binary switching"},
    {"id": "stored_program", "era": "mainframe", "mode": "shared batch storage"},
    {"id": "personal_shell", "era": "microcomputer", "mode": "local customization"},
    {"id": "networked_share", "era": "internet", "mode": "global information sharing"},
    {"id": "virtualized_mesh", "era": "council_os", "mode": "host-decoupled fluid adapters"},
)


@dataclass(frozen=True)
class CompatProfile:
    adapter: str
    host_decoupled: bool
    virtualized: bool
    restores_remnants: bool
    wipes_host: bool
    charter_citations: Tuple[str, ...]


class CompatibilityShell:
    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.active: Dict[str, CompatProfile] = {}

    def profile(self, adapter: str) -> CompatProfile:
        if adapter not in ADAPTERS:
            raise CharterViolation(f"unknown compatibility adapter {adapter}")
        return CompatProfile(
            adapter=adapter,
            host_decoupled=True,
            virtualized=True,
            restores_remnants=False,
            wipes_host=False,
            charter_citations=CHARTER_CITATIONS,
        )

    def enable(self, adapter: str) -> CompatProfile:
        profile = self.profile(adapter)
        self.active[adapter] = profile
        self.ledger.append(
            KernelDomain.SENTINEL,
            "COMPAT_ENABLE",
            {
                "adapter": adapter,
                "host_decoupled": True,
                "restores_remnants": False,
                "wipes_host": False,
            },
        )
        return profile

    def host_action(self, action: str) -> None:
        if action in FORBIDDEN_HOST_ACTIONS:
            raise CharterViolation("HOST_HARDWARE_DECOUPLED")
        raise CharterViolation("HOST_HARDWARE_DECOUPLED")

    def timeline(self) -> Dict[str, Any]:
        return {
            "epochs": list(COMPUTING_EPOCHS),
            "current": "virtualized_mesh",
            "host_decoupled": True,
            "capacity": "fluid_adapters_not_omnipotence",
            "inventor_customization": True,
            "matches_omnipotence": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active": {
                name: {
                    "host_decoupled": profile.host_decoupled,
                    "virtualized": profile.virtualized,
                    "restores_remnants": profile.restores_remnants,
                    "wipes_host": profile.wipes_host,
                }
                for name, profile in self.active.items()
            },
            "timeline": self.timeline(),
        }
