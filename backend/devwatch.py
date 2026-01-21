import subprocess
import time
import signal
import sys
from pathlib import Path
from threading import Timer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ===================== CONFIG =====================

WATCH_PATH = Path("backend")
COMMAND = [sys.executable, "backend/app.py"]
DEBOUNCE_SECONDS = 5.0

IGNORE_PATTERNS = (
    "__pycache__",
    ".git",
    ".venv",
    ".sqlite3",
    "-wal",
    "-shm",
)

# ===================== LOGIC =====================

class DebouncedReloader(FileSystemEventHandler):
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback
        self._timer = None

    def on_any_event(self, event):
        if any(p in event.src_path for p in IGNORE_PATTERNS):
            return

        if self._timer:
            self._timer.cancel()

        self._timer = Timer(DEBOUNCE_SECONDS, self.restart_callback)
        self._timer.start()


class AppRunner:
    def __init__(self):
        self.process = None

    def start(self):
        print("▶ starting app")
        self.process = subprocess.Popen(COMMAND)

    def stop(self):
        if self.process and self.process.poll() is None:
            print("■ stopping app")
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def restart(self):
        print(f"↻ restarting app (after {DEBOUNCE_SECONDS}s debounce)")
        self.stop()
        self.start()


# ===================== MAIN =====================

if __name__ == "__main__":
    runner = AppRunner()
    runner.start()

    event_handler = DebouncedReloader(runner.restart)
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()

    print(f"👀 watching {WATCH_PATH} (debounce={DEBOUNCE_SECONDS}s)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✋ shutting down")
        observer.stop()
        runner.stop()

    observer.join()
