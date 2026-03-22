import csv
from datetime import datetime

PLIK = "historia.csv"

def zapisz_historia(modul, objetosc, profil1, profil2="", wykonane=""):

    teraz = datetime.now()

    data = teraz.strftime("%Y-%m-%d")
    godzina = teraz.strftime("%H:%M")

    with open(PLIK, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            data,
            godzina,
            modul,
            objetosc,
            profil1,
            profil2,
            wykonane
        ])