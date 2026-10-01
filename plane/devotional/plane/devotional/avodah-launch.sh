#!/bin/bash
set -e
# AVODAH LAUNCH — canonical — b08a2817 — Selam OS — AVODAH-OS-8-CORE
# Auto-detects: prefers server.cjs (self-declaring CommonJS, immune to parent "type": "module"), fallback server.js
# Fixes: require is not defined crash when root package.json declares "type": "module"

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SERVER=""
if [ -f "$ROOT/server.cjs" ]; then
  SERVER="$ROOT/server.cjs"
  echo "[avodah] Using $SERVER (CJS immune)"
elif [ -f "$ROOT/server.js" ]; then
  SERVER="$ROOT/server.js"
  echo "
cd ~/yahweh-core || cd /root/yahweh-core || exit 1
mkdir -p plane/devotional
pwd

# --- CANONICAL avodah-launch.sh — first 40 lines review / recreation ---
cat > plane/devotional/avodah-launch.sh <<'LAUNCH'
#!/bin/bash
set -e
# AVODAH LAUNCH — canonical — b08a2817 — Selam OS — AVODAH-OS-8-CORE
# Auto-detects: prefers server.cjs (self-declaring CommonJS, immune to parent "type": "module"), fallback server.js
# Fixes: require is not defined crash when root package.json declares "type": "module"

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SERVER=""
if [ -f "$ROOT/server.cjs" ]; then
  SERVER="$ROOT/server.cjs"
  echo "[avodah] Using $SERVER (CJS immune)"
elif [ -f "$ROOT/server.js" ]; then
  SERVER="$ROOT/server.js"
  echo "[avodah] Using $SERVER (fallback)"
else
  echo "[avodah] ERROR: no server.cjs or server.js found in $ROOT" >&2
  ls -lh "$ROOT" >&2
  exit 1
fi

# Ensure node_modules if package.json exists
if [ -f "$ROOT/package.json" ] && [! -d "$ROOT/node_modules" ]; then
  echo "[avodah] Installing deps..."
  npm install --production
fi

# Health preflight
echo "[avodah] Node $(node -v) — Server $SERVER"
node --check "$SERVER" && echo "[avodah] Syntax OK ✓"

# Launch modes
MODE="${1:-start}"
case "$MODE" in
  --test|test)
    echo "[avodah] Running 17/17 verification..."
    # Tests run against server.cjs directly, bypassing parent ESM
    NODE_ENV=test node "$SERVER" --test 2>&1 | tail -100
    ;;
  start|*)
    echo "[avodah] Starting Selam OS — b08a2817 — $SERVER"
    exec node "$SERVER"
    ;;
esac
