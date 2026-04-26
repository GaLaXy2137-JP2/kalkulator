from math import ceil

from silnik.hil import get_adjusted_volume
from silnik.kalkulator import zbuduj_indeks_parametrow, znajdz_parametr

DEBUG = True

# =========================
# STAŁE SYSTEMU
# =========================

MARTWA = 50
BLOK_JONOWY_UL = 20

JONY = ["Chlorki", "Potas", "Sód"]


# =========================
# SILNIK ROZCIEŃCZEŃ
# =========================

def policz_rozcienczenia(objetosc, lista_parametrow, parametry, hemolysis=None, lipemia=None, icterus=None):
    indeks_parametrow = zbuduj_indeks_parametrow(parametry)

    # 🔥 TYLKO PROSTY FILTR (bez magii)
    lista_parametrow = [p for p in lista_parametrow if znajdz_parametr(p, parametry, indeks_parametrow)]

    wynik = {
        "robocza": 0,
        "nierozcienczalne": [],
        "nieroz_mieszczace": [],
        "tryb_nieroz": "brak",
        "bez_rozcienczenia": [],
        "do_rozcienczenia": [],
        "df": 0,
        "potrzebne_ul": 0,
        "blok_jonowy": None
    }

    # =========================
    # 1 OBJĘTOŚĆ ROBOCZA
    # =========================

    robocza = max(objetosc - MARTWA, 0)
    wynik["robocza"] = robocza

    # =========================
    # 2 BLOK JONOWY
    # =========================

    jony_w_profilu = [p for p in lista_parametrow if p in JONY]

    if len(jony_w_profilu) >= 2:

        wynik["blok_jonowy"] = {
            "nazwa": "Blok jonowy",
            "parametry": jony_w_profilu
        }

        lista_parametrow = [p for p in lista_parametrow if p not in JONY]

    # =========================
    # TRYB MAŁEJ PRÓBKI
    # =========================

    if objetosc <= MARTWA:

        roz = []
        nieroz = []

        if wynik["blok_jonowy"]:
            jony = ", ".join(wynik["blok_jonowy"]["parametry"])
            nieroz.append({
                "nazwa": f"Blok jonowy ({jony})",
                "ul": BLOK_JONOWY_UL
            })

        for p in lista_parametrow:
            parametr_key = znajdz_parametr(p, parametry, indeks_parametrow)

            if parametry[parametr_key]["rozc"] == 1:
                roz.append({
                    "nazwa": p,
                    "ul": get_adjusted_volume(
                        parametry[parametr_key]["ul"],
                        parametr_key,
                        hemolysis,
                        lipemia,
                        icterus,
                    ),
                })
            else:
                nieroz.append({
                    "nazwa": p,
                    "ul": get_adjusted_volume(
                        parametry[parametr_key]["ul"],
                        parametr_key,
                        hemolysis,
                        lipemia,
                        icterus,
                    ),
                })

        wynik["nierozcienczalne"] = nieroz
        wynik["do_rozcienczenia"] = roz
        wynik["tryb_nieroz"] = "zadne"

        potrzebne_ul = sum(p["ul"] for p in roz)
        wynik["potrzebne_ul"] = potrzebne_ul

        if potrzebne_ul > 0:

            docelowa = potrzebne_ul + MARTWA
            baza = MARTWA if objetosc > MARTWA else objetosc

            df = ceil(docelowa / baza)
            if df < 2:
                df = 2

            wynik["df"] = df
            wynik["baza"] = baza

        if "baza" not in wynik:
            wynik["baza"] = MARTWA if wynik["bez_rozcienczenia"] else objetosc

        return wynik

    # =========================
    # 3 NIERozcieńczalne
    # =========================

    nieroz = []

    if wynik["blok_jonowy"]:
        jony = ", ".join(wynik["blok_jonowy"]["parametry"])
        nieroz.append({
            "nazwa": f"Blok jonowy ({jony})",
            "ul": BLOK_JONOWY_UL
        })

    for p in lista_parametrow:
        parametr_key = znajdz_parametr(p, parametry, indeks_parametrow)
        if parametry[parametr_key]["rozc"] == 0:
            nieroz.append({
                "nazwa": p,
                "ul": get_adjusted_volume(
                    parametry[parametr_key]["ul"],
                    parametr_key,
                    hemolysis,
                    lipemia,
                    icterus,
                ),
            })

    nieroz.sort(key=lambda x: x["ul"])
    wynik["nierozcienczalne"] = nieroz

    # =========================
    # 4 MIESZCZĄCE SIĘ
    # =========================

    mieszczace = [p for p in nieroz if p["ul"] <= robocza]
    wynik["nieroz_mieszczace"] = mieszczace

    # =========================
    # 5 TRYB
    # =========================

    if len(nieroz) == 0:
        wynik["tryb_nieroz"] = "brak"
    elif len(mieszczace) == 0:
        wynik["tryb_nieroz"] = "zadne"
    elif sum(p["ul"] for p in mieszczace) <= robocza:
        wynik["tryb_nieroz"] = "wszystkie"
    else:
        wynik["tryb_nieroz"] = "wybor"

    # =========================
    # 6 OPERACYJNA
    # =========================

    suma = sum(p["ul"] for p in mieszczace)
    operacyjna = max(robocza - suma, 0)

    # =========================
    # 7 ROZCIEŃCZALNE
    # =========================

    roz = [
        {
            "nazwa": p,
            "ul": get_adjusted_volume(
                parametry[parametr_key]["ul"],
                parametr_key,
                hemolysis,
                lipemia,
                icterus,
            ),
        }
        for p in lista_parametrow
        for parametr_key in [znajdz_parametr(p, parametry, indeks_parametrow)]
        if parametr_key and parametry[parametr_key]["rozc"] == 1
    ]

    roz.sort(key=lambda x: x["ul"])

    # =========================
    # 8 BEZ ROZCIEŃCZENIA
    # =========================

    suma = 0
    for p in roz:
        if suma + p["ul"] <= operacyjna:
            wynik["bez_rozcienczenia"].append(p)
            suma += p["ul"]

    # =========================
    # 9 DO ROZCIEŃCZENIA
    # =========================

    nazwy_bez = [p["nazwa"] for p in wynik["bez_rozcienczenia"]]

    for p in roz:
        if p["nazwa"] not in nazwy_bez:
            wynik["do_rozcienczenia"].append(p)

    # =========================
    # 10 POTRZEBNE UL
    # =========================

    potrzebne_ul = sum(p["ul"] for p in wynik["do_rozcienczenia"])
    wynik["potrzebne_ul"] = potrzebne_ul

    # =========================
    # 🔥 11 DF (FINAL POPRAWNY)
    # =========================

    if potrzebne_ul > 0:

        docelowa = potrzebne_ul + MARTWA

        # 🔥 KLUCZ: rozcieńczenie zawsze z MARTWEJ
        baza = MARTWA

        df = ceil(docelowa / baza)

        if df < 2:
            df = 2

        wynik["df"] = df
        wynik["baza"] = baza

    # =========================
    # 12 PEŁNY PROFIL
    # =========================

    if (
        len(wynik["do_rozcienczenia"]) == 0
        and len(wynik["bez_rozcienczenia"]) > 0
        and wynik["tryb_nieroz"] != "zadne"
    ):
        wynik["pelny_profil"] = True
    else:
        wynik["pelny_profil"] = False

    if "baza" not in wynik:
        wynik["baza"] = MARTWA if wynik["bez_rozcienczenia"] else objetosc

    return wynik