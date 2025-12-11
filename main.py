from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uuid
import sys

from extract_logic import process_pdf_and_extract_rows, generate_excel_format_A_to_Q

app = FastAPI()

# --- Gestion des chemins suivant que l'on soit en script Python ou en EXE PyInstaller ---

if getattr(sys, "frozen", False):
    # Cas EXE (PyInstaller)
    # - sys._MEIPASS : dossier temporaire contenant les templates embarqués
    # - sys.executable : chemin du .exe -> on s'en sert pour uploads/output
    BASE_DIR = Path(sys._MEIPASS)                 # pour les templates
    APP_DIR = Path(sys.executable).resolve().parent  # dossier où se trouve le .exe
else:
    # Cas normal (lancé avec python main.py)
    BASE_DIR = Path(__file__).resolve().parent
    APP_DIR = BASE_DIR

# Dossiers pour les fichiers écrits par l'appli (toujours en dehors de MEIPASS)
UPLOAD_DIR = APP_DIR / "uploads"
OUTPUT_DIR = APP_DIR / "output"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Templates Jinja2 -> toujours à partir de BASE_DIR
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def form_upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/upload")
async def redirect_upload():
    return HTMLResponse(
        "<h3>Veuillez passer par <a href='/'>le formulaire</a>.</h3>"
    )

@app.post("/upload", response_class=HTMLResponse)
async def upload_files(request: Request, files: list[UploadFile] = File(...)):
    toutes_lignes = []
    nb_valid = 0

    for f in files:
        if not f.filename:
            continue

        nb_valid += 1
        pdf_path = UPLOAD_DIR / f.filename

        with open(pdf_path, "wb") as buffer:
            buffer.write(await f.read())

        lignes = process_pdf_and_extract_rows(pdf_path)
        toutes_lignes.extend(lignes)

    if nb_valid == 0:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "message": "❌ Aucun fichier sélectionné."}
        )

    excel_name = f"export_{uuid.uuid4().hex[:8]}.xlsx"
    excel_path = OUTPUT_DIR / excel_name

    generate_excel_format_A_to_Q(toutes_lignes, excel_path)

    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "message": f"✅ Traitement terminé : {len(toutes_lignes)} lignes extraites.",
            "download_link": f"/download/{excel_name}"
        }
    )


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return HTMLResponse("Fichier introuvable", status_code=404)
    return FileResponse(file_path, filename=filename)