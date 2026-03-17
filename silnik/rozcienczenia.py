from math import ceil

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

def policz_rozcienczenia(objetosc, lista_parametrow, parametry):

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

    if DEBUG:
        print("\n===== DEBUG ROZCIEŃCZEŃ =====")
        print("Objętość próbki:", objetosc)
        print("Objętość robocza:", robocza)

    # =========================
    # 2 BLOK JONOWY
    # =========================

    jony_w_profilu = [p for p in lista_parametrow if p in JONY]

    if len(jony_w_profilu) >= 2:

        wynik["blok_jonowy"] = {
            "nazwa": "Blok jonowy",
            "parametry": jony_w_profilu
        }

        lista_parametrow = [
            p for p in lista_parametrow
            if p not in JONY
        ]

        if DEBUG:
            print("Blok jonowy:", jony_w_profilu)

    elif len(jony_w_profilu) == 1:

        if DEBUG:
            print("Jeden jon:", jony_w_profilu)

    # =========================
    # 3 LISTA NIERozcieńczalnych
    # =========================

    nieroz = []

    if wynik["blok_jonowy"]:

        jony = ", ".join(wynik["blok_jonowy"]["parametry"])

        nieroz.append({
            "nazwa": f"Blok jonowy ({jony})",
            "ul": BLOK_JONOWY_UL
        })

    for p in lista_parametrow:

        if p not in parametry:
            continue

        if parametry[p]["rozc"] == 0:

            nieroz.append({
                "nazwa": p,
                "ul": parametry[p]["ul"]
            })

    nieroz.sort(key=lambda x: x["ul"])

    wynik["nierozcienczalne"] = nieroz

    # =========================
    # 4 KTÓRE SIĘ MIESZCZĄ
    # =========================

    mieszczace = []

    for p in nieroz:

        if p["ul"] <= robocza:
            mieszczace.append(p)

    wynik["nieroz_mieszczace"] = mieszczace

    if DEBUG:
        print("\nNierozcieńczalne:")
        for x in nieroz:
            print(x)

        print("\nMieszczące się:")
        for x in mieszczace:
            print(x)

    # =========================
    # 5 TRYB KROKU 1
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

    if DEBUG:
        print("\nOperacyjna:", operacyjna)

    # =========================
    # 7 LISTA ROZCIEŃCZALNYCH
    # =========================

    roz = []

    for p in lista_parametrow:

        if p not in parametry:
            continue

        if parametry[p]["rozc"] == 1:

            roz.append({
                "nazwa": p,
                "ul": parametry[p]["ul"]
            })

    roz.sort(key=lambda x: x["ul"])

    # =========================
    # 8 BEZ ROZCIEŃCZENIA
    # =========================

    suma = 0

    for p in roz:

        if suma + p["ul"] <= operacyjna:

            wynik["bez_rozcienczenia"].append(p)
            suma += p["ul"]

    if DEBUG:
        print("\nBez rozcieńczenia:")
        for x in wynik["bez_rozcienczenia"]:
            print(x)

    # =========================
    # 9 DO ROZCIEŃCZENIA
    # =========================

    nazwy_bez = [p["nazwa"] for p in wynik["bez_rozcienczenia"]]

    for p in roz:

        if p["nazwa"] not in nazwy_bez:
            wynik["do_rozcienczenia"].append(p)

    if DEBUG:
        print("\nDo rozcieńczenia:")
        for x in wynik["do_rozcienczenia"]:
            print(x)

    # =========================
    # 10 ILE UL POTRZEBA
    # =========================

    potrzebne_ul = sum(p["ul"] for p in wynik["do_rozcienczenia"])
    wynik["potrzebne_ul"] = potrzebne_ul

    if DEBUG:
        print("\nPotrzebne ul:", potrzebne_ul)

    # =========================
    # 11 WYLICZENIE DF
    # =========================

    if potrzebne_ul > 0:

        df = ceil((potrzebne_ul + MARTWA) / 50)

        if df < 2:
            df = 2

        wynik["df"] = df

        if DEBUG:
            print("DF:", df)

    return wynik