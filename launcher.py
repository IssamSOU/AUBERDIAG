import subprocess
import webbrowser
import time
import sys
import os

def main():
    # Lancer uvicorn dans un processus séparé
    server = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True
    )

    # Attendre que le serveur démarre
    time.sleep(2)

    # Ouvrir automatiquement la page web
    webbrowser.open("http://127.0.0.1:8000")

    # Garder l'exécutable actif
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()

if __name__ == "__main__":
    main()