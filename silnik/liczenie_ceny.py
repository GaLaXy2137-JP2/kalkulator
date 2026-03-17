import csv


def wczytaj_parametry():

    parametry = {}

    with open("parametry_ceny.csv", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        for r in reader:

            parametr = r["parametr"].strip()

            parametry[parametr] = {
                "odejmij": r["odejmij"],
                "dodaj": r["dodaj"]
            }

    return parametry


def wczytaj_profile_parametry():

    profile = {}

    with open("profile_parametry_ceny.csv", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        for r in reader:

            profil = r["profil"].strip()
            parametr = r["parametr"].strip()

            if profil not in profile:
                profile[profil] = []

            profile[profil].append(parametr)

    return profile


def wczytaj_ceny_profili():

    ceny = {}

    with open("profile_ceny.csv", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        for r in reader:

            profil = r["profil"].strip()

            ceny[profil] = float(r["cena"])

    return ceny


def wczytaj_ceny_morfologii():

    ceny = {}

    with open("morfologia_ceny.csv", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        for r in reader:

            typ = r["typ"].strip()

            ceny[typ] = float(r["dodaj"])

    return ceny


def wczytaj_profile_morfologia():

    dane = {}

    with open("profile_morfologia.csv", newline="", encoding="utf-8-sig") as f:

        reader = csv.DictReader(f)

        for row in reader:

            profil = row["profil"].strip()
            morf = int(row["morfologia"])

            dane[profil] = morf

    return dane


def filtruj_morfologie(lista, morfologia):

    wynik = []

    for p in lista:

        nazwa = p.lower()

        if "morfologia rozszerzona" in nazwa:

            if morfologia == "rozszerzona":
                wynik.append(p)

        elif "morfologia" in nazwa:

            if morfologia == "podstawowa":
                wynik.append(p)

        else:

            wynik.append(p)

    return wynik


def oblicz_cene(profil, wykonane, morfologia):

    parametry = wczytaj_parametry()
    profile = wczytaj_profile_parametry()
    ceny_profili = wczytaj_ceny_profili()
    ceny_morfologii = wczytaj_ceny_morfologii()

    lista = list(profile.get(profil, []))

    # dodanie morfologii do listy badań

    if morfologia == "podstawowa":
        lista.append("Morfologia")

    if morfologia == "rozszerzona":
        lista.append("Morfologia rozszerzona")

    cena_profilu = ceny_profili.get(profil, 0)

    # dodanie ceny morfologii do ceny z cennika

    if morfologia == "podstawowa":
        cena_profilu += ceny_morfologii.get("podstawowa", 0)

    if morfologia == "rozszerzona":
        cena_profilu += ceny_morfologii.get("rozszerzona", 0)

    liczba_parametrow = len(lista)

    wykonane = [p for p in wykonane if p in lista]

    liczba_wykonanych = len(wykonane)

    if liczba_parametrow == 0:
        return None

    procent = liczba_wykonanych / liczba_parametrow

    cena = 0

    # mniej niż 50% badań → suma pojedynczych

    if procent < 0.5:

        for p in wykonane:

            dane = parametry.get(p)

            if dane and dane["dodaj"] != "???":
                cena += float(dane["dodaj"])

    # powyżej 50% → cena profilu minus brakujące

    else:

        cena = cena_profilu

        for p in lista:

            if p not in wykonane:

                dane = parametry.get(p)

                if dane and dane["odejmij"] != "???":
                    cena -= float(dane["odejmij"])

    return {

        "cena_profilu": cena_profilu,
        "ilosc_parametrow": liczba_parametrow,
        "wykonane": liczba_wykonanych,
        "procent": round(procent * 100, 1),
        "cena_koncowa": round(cena, 2)

    }