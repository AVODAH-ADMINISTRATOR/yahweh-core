"""CLI: python -m council_os [status|compile|health|policy|audit|forge|covenant|library|ethiopic|housing|handset|workspace|cloudflare|schedule|business|compare|produce]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from council_os.constraints import CharterViolation
from council_os.forge import AutoDeveloperForge
from council_os.kernel import CouncilOSKernel
from council_os.ledger import LifecycleLedger
from council_os.policy import compile_policy, main as policy_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "status"
    if command == "policy":
        return policy_main(args[1:])
    if command == "audit":
        parser = argparse.ArgumentParser(prog="python -m council_os audit")
        parser.add_argument("--ledger", help="read and verify an existing JSONL ledger")
        options = parser.parse_args(args[1:])
        if options.ledger:
            policy_ok = False
            try:
                policy_ok = compile_policy()["status"] == "passed"
            except CharterViolation:
                pass
            try:
                if not Path(options.ledger).is_file():
                    raise CharterViolation("JSONL ledger file does not exist")
                ledger = LifecycleLedger(options.ledger)
                ledger_ok = ledger.verify_chain()
                count = len(ledger)
                head_hash = ledger.head_hash()
            except (CharterViolation, OSError) as exc:
                report = {
                    "status": "failed",
                    "checks": {"charter_policy": policy_ok, "ledger_chain": False,
                               "hmac_boot_seal": "not available for imported JSONL ledgers"},
                    "error": str(exc),
                }
                print(json.dumps(report, indent=2))
                return 1
            checks = {
                "charter_policy": policy_ok,
                "ledger_chain": ledger_ok,
                "hmac_boot_seal": "not available for imported JSONL ledgers",
            }
            report = {
                "status": "passed" if checks["charter_policy"] and checks["ledger_chain"] else "failed",
                "checks": checks,
                "ledger": {
                    "entries": count,
                    "head_hash": head_hash,
                    "record_ids": [
                        {"id": entry.entry_id, "domain": entry.domain}
                        for entry in ledger.entries
                    ],
                },
                "record_id_format": "sequence-domain-code-mnemonic-digit-sha256-prefix",
            }
        else:
            kernel = CouncilOSKernel()
            kernel.compile()
            report = kernel.audit_report()
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "passed" else 1
    kernel = CouncilOSKernel()
    if command == "compile":
        print(json.dumps(kernel.compile(), indent=2))
        return 0
    if command in {"status", "health"}:
        kernel.compile()
        print(json.dumps(kernel.health(), indent=2))
        return 0
    if command == "forge":
        forge = AutoDeveloperForge(kernel)
        print(json.dumps(forge.compile_workspace(), indent=2))
        return 0
    if command == "covenant":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.steward.covenant.snapshot(), indent=2))
        return 0
    if command == "library":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.library.snapshot(), indent=2))
        return 0
    if command == "ethiopic":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.ethiopic.snapshot(), indent=2))
        return 0
    if command == "housing":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.housing.snapshot(), indent=2))
        return 0
    if command == "handset":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.handset.snapshot(), indent=2))
        return 0
    if command == "workspace":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.workspace_catalog.snapshot(), indent=2))
        return 0
    if command == "cloudflare":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.cloudflare.snapshot(), indent=2))
        return 0
    if command == "schedule":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.scheduler.snapshot(), indent=2))
        return 0
    if command == "business":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.business.snapshot(), indent=2))
        return 0
    if command == "compare":
        forge = AutoDeveloperForge(kernel)
        forge.compile_workspace()
        print(json.dumps(forge.personal_ai.snapshot(), indent=2))
        return 0
    if command == "produce":
        forge = AutoDeveloperForge(kernel)
        print(json.dumps(forge.produce(), indent=2))
        return 0
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
