"""CLI: python -m council_os [status|compile|health|policy|forge|covenant]."""

from __future__ import annotations

import json
import sys

from council_os.forge import AutoDeveloperForge
from council_os.kernel import CouncilOSKernel
from council_os.policy import main as policy_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "status"
    if command == "policy":
        return policy_main(args[1:])
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
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
