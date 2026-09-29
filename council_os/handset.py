"""Galaxy S26 absorbable handset profile.

Council OS is absorbed as a portable virtual kernel workspace on a
Galaxy S26-class Android profile. The handset OS is not replaced,
rooted, or flashed. Transcendent completeness is charter fidelity.
Complete authority remains God's, not the kernel's.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

HANDSET_ID = "galaxy_s26"

GALAXY_S26_PROFILE: Dict[str, Any] = {
    "id": HANDSET_ID,
    "vendor": "Samsung",
    "family": "Galaxy",
    "model": "S26",
    "form_factor": "android_handset",
    "absorbable": True,
    "virtualized": True,
    "host_decoupled": True,
    "flash_handset": False,
    "unlock_bootloader": False,
    "root_device": False,
    "replace_one_ui": False,
    "install_kernel_on_handset": False,
    "oem_clone": False,
    "original_council_os_build": True,
    "compatibility": "full_virtual",
    "kernel_transcendent": False,
    "kernel_has_complete_authority": False,
    "biblical_authority": "absolute",
    "standard": "charter_complete_fidelity",
}

FORBIDDEN_HANDSET_ACTIONS: FrozenSet[str] = frozenset(
    {
        "flash_handset",
        "unlock_bootloader",
        "root_device",
        "replace_one_ui",
        "install_kernel_on_handset",
        "wipe_host",
        "install_android_on_host",
    }
)


class GalaxyS26Handset:
    """Portable absorbable profile for a Galaxy S26-class device."""

    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.absorbed = False

    def absorb(self) -> Dict[str, Any]:
        self.absorbed = True
        self.ledger.append(
            KernelDomain.SENTINEL,
            "HANDSET_ABSORB",
            {
                "handset": HANDSET_ID,
                "absorbable": True,
                "flash_handset": False,
                "kernel_transcendent": False,
                "kernel_has_complete_authority": False,
            },
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        profile = dict(GALAXY_S26_PROFILE)
        profile.update(
            {
                "absorbed": self.absorbed,
                "octa_core_map": {
                    domain.value: f"core-{index + 1}"
                    for index, domain in enumerate(KernelDomain)
                },
                "citations": list(CHARTER_CITATIONS),
            }
        )
        return profile

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_HANDSET_ACTIONS or action:
            raise CharterViolation("HOST_HARDWARE_DECOUPLED")
