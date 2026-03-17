import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from silnik.rozcienczenia import policz_rozcienczenia
import csv

# wczytanie parametrów
parametry = {}

with open("parametry.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for r in reader:
        parametry[r["Parametr"]] = {
            "ul": float(r["Olimpus B"]),
            "jon": int(r["Czy jon"]),
            "rozc": int(r["Czy rozcienczalne"])
        }

# wczytanie profili
profile = {}

with open("profile.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for r in reader:

        profil = r["Profil"]
        parametr = r["Parametr"]

        if profil not in profile:
            profile[profil] = []

        profile[profil].append(parametr)

print("\n===== TEST ROZCIEŃCZEŃ =====\n")

profil = "Geriatria podstawowa"

lista = profile[profil]

wynik = policz_rozcienczenia(
    objetosc=120,
    lista_parametrow=lista,
    parametry=parametry
)

print("Profil:", profil)
print("Parametry:", lista)
print()

print("Objętość robocza:", wynik["robocza"])

print("\nNierozcieńczalne:")
for p in wynik["nierozcienczalne"]:
    print(p)

print("\nBez rozcieńczenia:")
for p in wynik["bez_rozcienczenia"]:
    print(p)

print("\nDo rozcieńczenia:")
for p in wynik["do_rozcienczenia"]:
    print(p)

print("\nPotrzebne ul:", wynik["potrzebne_ul"])
print("DF:", wynik["df"])