import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path

def main():
    # Empêche de relancer plusieurs fois le navigateur
    marker_file = Path("browser_opened.marker")

    base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    os.chdir(base_dir)

    # Lancer uvicorn SANS reload (très important)
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--no-reload",         # 🔥 empêche le reloader (cause des boucles)
            "--log-level", "warning"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Attendre que le serveur soit prêt
    time.sleep(2)

    # Ouvrir le navigateur UNE SEULE FOIS
    if not marker_file.exists():
        webbrowser.open("http://127.0.0.1:8000")
        marker_file.touch()

    # Maintenir le processus
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()

if __name__ == "__main__":
    main()