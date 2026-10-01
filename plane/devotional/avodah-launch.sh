#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$ROOT"
if [ -f server.cjs ]; then S=server.cjs; else S=server.js; fi
node --check $S; echo "[avodah] $S OK"; NODE_ENV=test node $S --test 2>&1 || node $S
