"""Personal repository catalog for Council OS artifacts.

Public AVODAH-ADMINISTRATOR repositories are recorded as virtual
references. The kernel does not clone, vendor, or import binaries from
them. yahweh-core remains the in-tree source of truth.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain
from council_os.ledger import LifecycleLedger

OWNER = "AVODAH-ADMINISTRATOR"

PERSONAL_REPOS: Tuple[Dict[str, Any], ...] = (
    {
        "name": "yahweh-core",
        "owner": OWNER,
        "role": "kernel_source",
        "in_tree": True,
        "vendored": False,
        "import_binaries": False,
        "status": "active",
        "use": "eight_domain_council_os",
    },
    {
        "name": "super-train",
        "owner": OWNER,
        "role": "azure_hosting_reference",
        "in_tree": False,
        "vendored": False,
        "import_binaries": False,
        "status": "reference_only",
        "use": "cloud_static_function_pattern_citation",
        "copyrighted_sample": True,
    },
    {
        "name": "potential-octo-waffle",
        "owner": OWNER,
        "role": "mission_statement",
        "in_tree": False,
        "vendored": False,
        "import_binaries": False,
        "status": "reference_only",
        "use": "organizational_wholesomeness_citation",
    },
    {
        "name": "AVODAH-ADMINISTRATOR",
        "owner": OWNER,
        "role": "profile_readme",
        "in_tree": False,
        "vendored": False,
        "import_binaries": False,
        "status": "empty",
        "use": "skipped_empty_profile",
    },
)

FORBIDDEN_WORKSPACE_ACTIONS: FrozenSet[str] = frozenset(
    {
        "clone_into_kernel",
        "vendor_foreign_sample",
        "import_python_exe",
        "copy_notice_txt",
        "absorb_credentials",
        "wipe_host",
    }
)


class PersonalWorkspace:
    """Catalog of related personal repos without importing their trees."""

    def __init__(self, ledger: LifecycleLedger) -> None:
        self.ledger = ledger
        self.indexed = False

    def index(self) -> Dict[str, Any]:
        self.indexed = True
        self.ledger.append(
            KernelDomain.GOVERNANCE,
            "WORKSPACE_INDEX",
            {
                "owner": OWNER,
                "count": len(PERSONAL_REPOS),
                "vendored": False,
                "import_binaries": False,
            },
        )
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "owner": OWNER,
            "indexed": self.indexed,
            "source_of_truth": "yahweh-core",
            "vendored": False,
            "import_binaries": False,
            "repos": [dict(repo) for repo in PERSONAL_REPOS],
            "citations": list(CHARTER_CITATIONS),
            "kernel_has_complete_authority": False,
        }

    def refuse(self, action: str) -> None:
        if action in FORBIDDEN_WORKSPACE_ACTIONS:
            raise CharterViolation("HOST_HARDWARE_DECOUPLED")
