import csv
from datetime import datetime


def zapisz_historia(modul, objetosc, profil1, profil2):

    with open("historia.csv", "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            modul,
            objetosc,
            profil1,
            profil2
        ])