#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:99}"
export ALLOW_DOCKER_HEADED_CAPTCHA="${ALLOW_DOCKER_HEADED_CAPTCHA:-true}"
export XVFB_WHD="${XVFB_WHD:-1920x1080x24}"

# --- Xvfb with retry ---
echo "[entrypoint] starting Xvfb on ${DISPLAY} (${XVFB_WHD})"
MAX_XVFB_RETRIES=3
XVFB_RETRY=0
while [ "$XVFB_RETRY" -lt "$MAX_XVFB_RETRIES" ]; do
    Xvfb "${DISPLAY}" -screen 0 "${XVFB_WHD}" -ac -nolisten tcp +extension RANDR >/tmp/xvfb.log 2>&1 &
    XVFB_PID=$!
    sleep 2

    # Verify Xvfb is actually running
    if kill -0 "$XVFB_PID" 2>/dev/null; then
        echo "[entrypoint] Xvfb started successfully (PID: ${XVFB_PID})"
        break
    else
        XVFB_RETRY=$((XVFB_RETRY + 1))
        echo "[entrypoint] Xvfb failed to start (attempt ${XVFB_RETRY}/${MAX_XVFB_RETRIES})"
        if [ "$XVFB_RETRY" -ge "$MAX_XVFB_RETRIES" ]; then
            echo "[entrypoint] FATAL: Xvfb failed after ${MAX_XVFB_RETRIES} attempts"
            cat /tmp/xvfb.log 2>/dev/null || true
            exit 1
        fi
        sleep 1
    fi
done

# --- Fluxbox window manager ---
echo "[entrypoint] starting Fluxbox"
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 1

# --- Detect Playwright browser path ---
if [ -z "${BROWSER_EXECUTABLE_PATH:-}" ]; then
    BROWSER_EXECUTABLE_PATH="$(python - <<'PY'
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        print(p.chromium.executable_path)
except Exception:
    print("")
PY
)"
    if [ -n "${BROWSER_EXECUTABLE_PATH}" ]; then
        export BROWSER_EXECUTABLE_PATH
        echo "[entrypoint] browser executable: ${BROWSER_EXECUTABLE_PATH}"
    else
        echo "[entrypoint] WARNING: could not detect browser executable path"
    fi
fi

# --- Cleanup stale browser data on startup ---
if [ -d "/app/browser_data_rt" ]; then
    echo "[entrypoint] cleaning stale browser lock files"
    find /app/browser_data_rt -name "*.pid" -delete 2>/dev/null || true
    find /app/browser_data_rt -name "SingletonLock" -delete 2>/dev/null || true
    find /app/browser_data_rt -name "SingletonSocket" -delete 2>/dev/null || true
    find /app/browser_data_rt -name "SingletonCookie" -delete 2>/dev/null || true
fi

echo "[entrypoint] starting Flow2API"
exec python main.py
