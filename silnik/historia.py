import csv
from datetime import datetime


def zapisz_historia(modul, objetosc, profil1, profil2, parametry=None):

    import csv
    from datetime import datetime

    if parametry is None:
        parametry = []

    parametry_str = ", ".join(parametry)

    with open("historia.csv", "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            modul,
            objetosc,
            profil1,
            profil2,
            parametry_str
        ])