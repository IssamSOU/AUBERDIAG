import pdfplumber
import re
from pathlib import Path
from openpyxl import Workbook
from datetime import date


IMMATRICULATION_REGEX = r"[A-Z]{2}-?\d{3}-?[A-Z]{2}"


# -----------------------------
# Détection fournisseur
# -----------------------------
def detect_fournisseur(text: str) -> str:
    t = text.upper()
    if "VROOMLY" in t or "DOCAUTO" in t:
        return "vroomly"
    if "SOPARTEX" in t:
        return "sopartex"
    return "unknown"


# -----------------------------
# Parser VROOMLY
# -----------------------------
def parse_vroomly(text: str):
    """
    Gère les 2 formats Vroomly :

    1) Avec véhicule + immatriculation :
       Kit de roulements de roue
       SKF VKBA 6786 GH-304-CK 2 70,12 20% 140,24

       -> description = "Kit de roulements de roue SKF VKBA 6786"
       -> immatriculation = GH-304-CK

    2) Sans véhicule (pneus) :
       Pneus
       LING LONG Grnmaxxas
       175/65R14 82T
       2 32,20 20% 64,40

       -> description = "Pneus LING LONG Grnmaxxas 175/65R14 82T"
       -> pas d'immatriculation
    """
    lines = [l.strip() for l in text.splitlines() if (l or "").strip()]
    items = []

    # 1) On cherche la ligne d'en-tête "Description ... Qté ..."
    start_idx = 0
    for i, line in enumerate(lines):
        u = line.upper()
        if "DESCRIPTION" in u and "QTÉ" in u:
            start_idx = i + 1
            break

    # 2) Patterns pour les lignes de détail
    pattern_with_vehicle = re.compile(
        r"^(?P<vehicule>.+?)\s+(?P<qte>\d+)\s+(?P<pu>\d+[.,]\d+)\s+\d+%\s+(?P<total>\d+[.,]\d+)$"
    )
    pattern_no_vehicle = re.compile(
        r"^(?P<qte>\d+)\s+(?P<pu>\d+[.,]\d+)\s+\d+%\s+(?P<total>\d+[.,]\d+)$"
    )

    desc_buffer = []

    for line in lines[start_idx:]:
        # Ligne détail AVEC véhicule (ex: SKF VKBA 6786 GH-304-CK 2 70,12 20% 140,24)
        m1 = pattern_with_vehicle.match(line)
        if m1:
            vehicule = m1.group("vehicule").strip()
            qte = int(m1.group("qte"))
            pu = float(m1.group("pu").replace(",", "."))

            # Immatriculation éventuellement dans vehicule
            imm_match = re.search(IMMATRICULATION_REGEX, vehicule)
            immatriculation = imm_match.group() if imm_match else None

            if immatriculation:
                vehicule_base = vehicule.replace(immatriculation, "").strip()
            else:
                vehicule_base = vehicule

            # Description = toutes les lignes du buffer + vehicule_base
            desc_text = " ".join(desc_buffer).strip()
            if desc_text:
                core_designation = (desc_text + " " + vehicule_base).strip()
            else:
                core_designation = vehicule_base

            # Désignation finale : Vroomly - <core> (- immat si existe)
            if immatriculation:
                designation_finale = f"Vroomly - {core_designation} - {immatriculation}"
            else:
                designation_finale = f"Vroomly - {core_designation}"

            # Référence : on peut prendre vehicule_base (ou une partie, à affiner)
            reference = vehicule_base if vehicule_base else "REF-INCONNUE"

            items.append(
                {
                    "reference": reference,
                    "designation": designation_finale,
                    "quantite": qte,
                    "prix_achat_ht": pu,
                }
            )

            desc_buffer = []
            continue

        # Ligne détail SANS véhicule (ex: 2 32,20 20% 64,40)
        m2 = pattern_no_vehicle.match(line)
        if m2:
            qte = int(m2.group("qte"))
            pu = float(m2.group("pu").replace(",", "."))

            desc_text = " ".join(desc_buffer).strip()
            core_designation = desc_text if desc_text else "Article Vroomly"

            designation_finale = f"Vroomly - {core_designation}"

            # Référence : on peut utiliser la dernière ligne de description (ex: dimension du pneu)
            if desc_buffer:
                reference = desc_buffer[-1]
            else:
                reference = "REF-INCONNUE"

            items.append(
                {
                    "reference": reference,
                    "designation": designation_finale,
                    "quantite": qte,
                    "prix_achat_ht": pu,
                }
            )

            desc_buffer = []
            continue

        # Sinon, on considère que c'est une ligne de description d'article
        desc_buffer.append(line)

    return items


# -----------------------------
# Parser SOPARTEX
# -----------------------------
def parse_sopartex(text: str):
    lines = [l.strip() for l in text.splitlines() if (l or "").strip()]
    items = []

    pattern = re.compile(
        r"^(?P<ref>\d+)\s+(?P<qte>\d+)\s+(?P<des>.+?)\s+(?P<pu>\d+[.,]\d+)\s+(?P<total>\d+[.,]\d+)(?:\s+P)?$"
    )

    for line in lines:
        m = pattern.match(line)
        if not m:
            continue

        reference = m.group("ref")
        quantite = int(m.group("qte"))
        designation_base = m.group("des").strip()
        prix_ht = float(m.group("pu").replace(",", "."))

        designation_finale = f"Sopartex - {designation_base}"

        items.append(
            {
                "reference": reference,
                "designation": designation_finale,
                "quantite": quantite,
                "prix_achat_ht": prix_ht,
            }
        )

    return items


# -----------------------------
# Router : choisir le parser
# -----------------------------
def process_pdf_and_extract_rows(pdf_path: Path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"

    fournisseur = detect_fournisseur(full_text)

    if fournisseur == "vroomly":
        return parse_vroomly(full_text)
    if fournisseur == "sopartex":
        return parse_sopartex(full_text)

    return []


# -----------------------------
# Génération Excel A → Q
# -----------------------------
def generate_excel_format_A_to_Q(rows, excel_path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Catalogue"



    today = date.today().strftime("%Y%m%d")

    for item in rows:
        ws.append(
            [
                item.get("reference", ""),       # A
                item.get("designation", ""),     # B
                "AUTO",                          # C Code fournisseur
                "",                              # D
                0,                               # E Taux remise
                "",                              # F
                item.get("prix_achat_ht", ""),   # G
                "",                              # H
                today,                           # I
                "",                              # J
                item.get("quantite", ""),        # K
                "", "", "", "",                  # L–O
                "",                              # P
                "",                              # Q
            ]
        )

    wb.save(excel_path)