#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m py_
python -m pytest -q

# Interactive authentication, once:
python yahweh_core.py --authenticate

# Mandatory first production run: PLAN ONLY.
python yahweh_core.py --json

# Controlled execution. Local deletion remains OFF.
python yahweh_core.py --apply

# DO NOT enable this until backups and recovery have been verified:
# python yahweh_core.py --apply --delete-local-after-upload
