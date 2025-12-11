import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path
import socket

def is_port_in_use(port: int) -> bool:
    """Vérifie si le port 8000 est déjà occupé (donc uvicorn tourne déjà)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0

def main():
    base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    os.chdir(base_dir)

    # ⚠️ Empêche 2 instances du programme
    lock_file = base_dir / "auberdiag.lock"
    if lock_file.exists():
        print("L'application est déjà en cours d'exécution.")
        # Ouvre simplement le navigateur si uvicorn tourne déjà
        if is_port_in_use(8000):
            webbrowser.open("http://127.0.0.1:8000")
        return

    # Crée un verrou pour éviter toute seconde instance
    lock_file.touch()

    # Si uvicorn n'est PAS déjà lancé → le démarrer
    if not is_port_in_use(8000):
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--no-reload",      # empêcher reloader
                "--no-use-colors"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Attente du démarrage du serveur
        for _ in range(20):  # ~2 secondes max
            if is_port_in_use(8000):
                break
            time.sleep(0.1)

    # Ouvre le navigateur UNE SEULE FOIS
    webbrowser.open("http://127.0.0.1:8000")

    try:
        # Attend la fin du process uvicorn
        server.wait()
    except:
        pass
    finally:
        if lock_file.exists():
            lock_file.unlink()

if __name__ == "__main__":
    main()