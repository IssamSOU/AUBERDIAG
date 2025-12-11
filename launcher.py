import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path

def main():
    # Pour PyInstaller : lancer depuis le dossier du .exe
    base_dir = Path(sys.executable).resolve().parent
    os.chdir(base_dir)

    # Lancer le serveur uvicorn
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Donne 1-2 secondes au serveur pour démarrer
    time.sleep(2)

    # Ouvre automatiquement le navigateur
    webbrowser.open("http://127.0.0.1:8000")

    # Maintient l’application active
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()

if __name__ == "__main__":
    main()