"""Launch 3 Streamlit instances for KMS Tử Vi with KMS_UI_FIXTURE=1 as detached processes."""
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT_DIR = r"d:\Ki7\KMS_Tu_Vi"

# Flags for detached background process on Windows:
# DETACHED_PROCESS (0x00000008) | CREATE_NEW_PROCESS_GROUP (0x00000200) | CREATE_NO_WINDOW (0x08000000)
FLAGS = 0x00000008 | 0x00000200 | 0x08000000

env = os.environ.copy()
env["KMS_UI_FIXTURE"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

servers = [
    ("8501", ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true", "--server.address", "127.0.0.1"]),
    ("8502", ["streamlit", "run", "frontend/lasoban.py", "--server.port", "8502", "--server.headless", "true", "--server.address", "127.0.0.1"]),
    ("8503", ["streamlit", "run", "frontend/app.py", "--server.port", "8503", "--server.headless", "true", "--server.address", "127.0.0.1"]),
]

log_dir = Path(ROOT_DIR) / ".taste-skill" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

for port, cmd in servers:
    out_f = open(log_dir / f"streamlit_{port}.log", "w", encoding="utf-8")
    p = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        env=env,
        creationflags=FLAGS,
        stdout=out_f,
        stderr=out_f,
        stdin=subprocess.DEVNULL,
    )
    print(f"Launched port {port} with PID {p.pid}")

time.sleep(3)
print("All 3 servers launched.")
