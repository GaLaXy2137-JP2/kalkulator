import json
from datetime import datetime
import os

PLIK = "historia.json"


def zapisz_historia(modul, objetosc, profil1, profil2, parametry, wynik=None, morfologia=None):

    wpis = {
    "data": datetime.now().strftime("%Y-%m-%d"),
    "godzina": datetime.now().strftime("%H:%M"),
    "modul": modul,
    "objetosc": objetosc,
    "profil1": profil1,
    "profil2": profil2,
    "parametry": parametry,
    "wynik": wynik,
    "morfologia": morfologia
}

    # 🔥 wczytaj stare
    if os.path.exists(PLIK):
        with open(PLIK, encoding="utf-8") as f:
            try:
                dane = json.load(f)
            except:
                dane = []
    else:
        dane = []

    # 🔥 dodaj nowy wpis
    dane.append(wpis)

    # 🔥 zapisz
    with open(PLIK, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=2)