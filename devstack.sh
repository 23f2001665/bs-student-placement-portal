#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="$ROOT_DIR/.venv/bin"
FRONTEND_DIR="$ROOT_DIR/frontend"
API_PORT="${API_PORT:-5000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
REDIS_PID_FILE="$ROOT_DIR/.devstack_redis.pid"
STOP_EXISTING_REDIS="${DEVSTACK_STOP_EXISTING_REDIS:-1}"

declare -a STARTED_NAMES=()
declare -a STARTED_PIDS=()
REDIS_STARTED_BY_SCRIPT=0
REDIS_PID=""
SHUTTING_DOWN=0

log() {
  printf '[devstack] %s\n' "$*"
}

port_in_use() {
  local port="$1"

  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :${port}" | awk 'NR>1 {print $4}' | grep -q ":${port}$"
    return
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
    return
  fi

  return 1
}

ensure_port_free() {
  local port="$1"
  local name="$2"

  if port_in_use "$port"; then
    log "${name} port ${port} is already in use. Stop the existing process and rerun devstack."
    exit 1
  fi
}

verify_process_started() {
  local pid="$1"
  local name="$2"
  local grace_seconds="${3:-2}"

  sleep "$grace_seconds"
  if ! kill -0 "$pid" 2>/dev/null; then
    log "${name} exited during startup. Aborting stack launch."
    exit 1
  fi
}

resolve_redis_pid() {
  if [[ -f "$REDIS_PID_FILE" ]]; then
    cat "$REDIS_PID_FILE"
    return
  fi

  if command -v redis-cli >/dev/null 2>&1; then
    redis-cli INFO server 2>/dev/null | awk -F: '/^process_id:/ {gsub(/\r/,"",$2); print $2; exit}'
    return
  fi

  printf ''
}

start_process() {
  local name="$1"
  shift

  log "Starting ${name}..."
  "$@" &
  local pid=$!

  STARTED_NAMES+=("$name")
  STARTED_PIDS+=("$pid")

  log "${name} started (pid=${pid})"

  verify_process_started "$pid" "$name"
}

stop_process() {
  local pid="$1"
  local name="$2"

  if kill -0 "$pid" 2>/dev/null; then
    log "Stopping ${name} (pid=${pid})..."
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    log "${name} stopped"
  fi
}

shutdown_all() {
  if [[ "$SHUTTING_DOWN" -eq 1 ]]; then
    return
  fi
  SHUTTING_DOWN=1

  if [[ ${#STARTED_PIDS[@]} -gt 0 || "$REDIS_STARTED_BY_SCRIPT" -eq 1 ]]; then
    log "Termination received, shutting down services in reverse order..."
  fi

  for (( idx=${#STARTED_PIDS[@]}-1 ; idx>=0 ; idx-- )); do
    stop_process "${STARTED_PIDS[$idx]}" "${STARTED_NAMES[$idx]}"
  done

  if [[ "$REDIS_STARTED_BY_SCRIPT" -eq 1 || "$STOP_EXISTING_REDIS" -eq 1 ]]; then
    redis_pid="${REDIS_PID:-$(resolve_redis_pid)}"
    log "Stopping redis-server..."

    if command -v redis-cli >/dev/null 2>&1; then
      redis-cli shutdown nosave >/dev/null 2>&1 || true
    fi

    if [[ -n "$redis_pid" ]] && kill -0 "$redis_pid" 2>/dev/null; then
      kill "$redis_pid" 2>/dev/null || true
      wait "$redis_pid" 2>/dev/null || true
    fi

    rm -f "$REDIS_PID_FILE"
    log "redis-server stopped"
  fi

  if [[ ${#STARTED_PIDS[@]} -gt 0 || "$REDIS_STARTED_BY_SCRIPT" -eq 1 ]]; then
    log "All services stopped"
  fi
}

trap shutdown_all INT TERM EXIT

if ! command -v pnpm >/dev/null 2>&1; then
  log "pnpm not found in PATH"
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  log "uv not found in PATH"
  exit 1
fi

log "Syncing Python dependencies with uv..."
(
  cd "$ROOT_DIR"
  uv sync
)

if [[ ! -f "$ROOT_DIR/.venv/bin/activate" ]]; then
  log "Python virtual environment not found at $ROOT_DIR/.venv"
  log "uv sync did not create .venv as expected"
  exit 1
fi

log "Activating Python virtual environment..."
# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"
VENV_BIN="$VIRTUAL_ENV/bin"

log "Installing frontend dependencies with pnpm..."
(
  cd "$FRONTEND_DIR"
  pnpm install
)

ensure_port_free "$API_PORT" "Flask"
ensure_port_free "$FRONTEND_PORT" "Frontend"

if ! command -v redis-cli >/dev/null 2>&1 || ! redis-cli ping >/dev/null 2>&1; then
  if command -v redis-server >/dev/null 2>&1; then
    log "Redis not reachable, starting local redis-server..."
    redis-server --save "" --appendonly no --daemonize yes --pidfile "$REDIS_PID_FILE"
    REDIS_STARTED_BY_SCRIPT=1
    REDIS_PID="$(resolve_redis_pid)"
  else
    log "Redis is not running and redis-server binary was not found"
    exit 1
  fi
else
  if [[ "$STOP_EXISTING_REDIS" -eq 1 ]]; then
    REDIS_PID="$(resolve_redis_pid)"
    log "Using existing redis-server instance. It will be stopped when devstack exits."
  else
    log "Using existing redis-server instance. It will remain running after devstack exits."
  fi
fi

start_process "Flask API" "$VENV_BIN/python" -m backend.app
start_process "Celery Worker" "$VENV_BIN/celery" -A backend.celery_worker.celery worker --loglevel=info --concurrency=4
start_process "Celery Beat" "$VENV_BIN/celery" -A backend.celery_worker.celery beat --loglevel=info
start_process "Frontend (Vite)" bash -lc "cd '$FRONTEND_DIR' && pnpm dev -- --strictPort --port ${FRONTEND_PORT}"

log "All services are up. Press Ctrl+C to stop everything."

while true; do
  sleep 1
  for pid in "${STARTED_PIDS[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      log "A service exited unexpectedly. Stopping the stack."
      exit 1
    fi
  done
done
