"""Dell OptiPlex 5040 mini-tower housing skeleton.

The chassis is reused as a physical shell. Council OS is an original
build profile-matched to that skeleton — not an OEM Windows/Android
clone, and not a reason to discard working components.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

SKELETON_ID = "dell_optiplex_5040_mt"

OPTIPLEX_5040_PROFILE: Dict[str, Any] = {
    "id": SKELETON_ID,
    "vendor": "Dell",
    "family": "OptiPlex",
    "model": "5040",
    "form_factor": "mini_tower",
    "chipset": "intel_q170",
    "cpu_generation": "skylake_6th",
    "memory": "ddr3l_up_to_16gb",
    "storage": "sata",
    "discrete_gpu": False,
    "oem_shell_working": False,
    "reuse_chassis": True,
    "waste_skeleton": False,
    "oem_clone": False,
    "original_council_os_build": True,
    "host_wipe": False,
    "install_android_on_host": False,
    "reliability": "profile_matched_virtual_kernel",
}

FORBIDDEN_SKELETON_ACTIONS: FrozenSet[str] = frozenset(
    {
        "discard_chassis",
        "waste_skeleton",
        "clone_oem_image",
        "restore_dell_factory_windows",
        "wipe_host",
        "install_android_on_host",
    }
)


class OptiplexHousing:
    """Original Council OS build housed in a 5040-class skeleton."""

    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.seated = False

    def seat(self) -> Dict[str, Any]:
        self.seated = True
        self.ledger.append(
            KernelDomain.SENTINEL,
            "SKELETON_SEAT",
            {
                "skeleton": SKELETON_ID,
                "original_build": True,
                "oem_clone": False,
                "waste_skeleton": False,
            },
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        profile = dict(OPTIPLEX_5040_PROFILE)
        profile.update(
            {
                "seated": self.seated,
                "octa_core_map": {
                    domain.value: f"core-{index + 1}"
                    for index, domain in enumerate(KernelDomain)
                },
                "gpu_on_chassis": False,
                "citations": list(CHARTER_CITATIONS),
                "host_decoupled": True,
                "virtualized": True,
            }
        )
        return profile

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_SKELETON_ACTIONS or action:
            raise CharterViolation("HOST_HARDWARE_DECOUPLED")
