#!/usr/bin/env python3
import pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
QUADS = [
    "services/governance",
    "services/bluetooth/nodes",
    "services/drive",
    "services/api",
    "services/execution",
    "council_os/seals",
    "council_os",
    "kernel",
]


def main():
    print("=== YAHWEH-CORE | Welcome Home ===")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Configured quadrants: {len(QUADS)}")
    print("")
    ok = True
    for q in QUADS:
        p = ROOT / q
        c = len(list(p.glob("*"))) if p.is_dir() else 0
        ready = c > 0
        ok = ok and ready
        print(f"  {q}: {c} entries - {'READY' if ready else 'MISSING'}")
    print("")
    print("Bootstrap inspection complete." if ok else "Bootstrap inspection incomplete.")
    print(f"SUCCESS: {str(ok).lower()}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
