from silnik.hil import get_adjusted_volume, normalize_param_name


# =========================
# ODMIANA LICZEBNIKA
# =========================

def odmien_badanie(n):

    if n % 100 in (12,13,14):
        return "badań"

    if n % 10 == 1:
        return "badanie"

    if n % 10 in (2,3,4):
        return "badania"

    return "badań"


# =========================
# BUDOWANIE LISTY PARAMETRÓW
# =========================

def zbuduj_liste_parametrow(profil1, profil2, parametry_wybrane, profile_map):

    lista = []

    # profil 1
    if profil1 and profil1 in profile_map:
        lista += profile_map[profil1]

    # profil 2
    if profil2 and profil2 in profile_map:
        lista += profile_map[profil2]

    # parametry ręczne
    if parametry_wybrane:
        lista += parametry_wybrane

    # usuwanie duplikatów (z zachowaniem kolejności)
    seen = set()
    wynik = []

    for p in lista:
        if p not in seen:
            seen.add(p)
            wynik.append(p)

    return wynik


def zbuduj_indeks_parametrow(parametry):
    return {normalize_param_name(nazwa): nazwa for nazwa in parametry}


def znajdz_parametr(nazwa_parametru, parametry, indeks_parametrow=None):
    if nazwa_parametru in parametry:
        return nazwa_parametru

    if indeks_parametrow is None:
        indeks_parametrow = zbuduj_indeks_parametrow(parametry)

    return indeks_parametrow.get(normalize_param_name(nazwa_parametru))


# =========================
# OBJĘTOŚĆ PEŁNEGO PROFILU
# =========================

def objetosc_pelnego_profilu(lista, parametry, hemolysis=None, lipemia=None, icterus=None):

    suma = 0
    ma_jony = False
    indeks_parametrow = zbuduj_indeks_parametrow(parametry)

    for p in lista:
        parametr_key = znajdz_parametr(p, parametry, indeks_parametrow)

        if not parametr_key:
            continue

        if parametry[parametr_key]["jon"] == 1:
            ma_jony = True
        else:
            suma += get_adjusted_volume(
                parametry[parametr_key]["ul"],
                parametr_key,
                hemolysis,
                lipemia,
                icterus,
            )

    suma += 50

    if ma_jony:
        suma += 20

    return suma


# =========================
# SILNIK LICZENIA (Excel)
# =========================

def licz_zakres_excel(objetosc, lista_parametrow, parametry, hemolysis=None, lipemia=None, icterus=None):

    robocza = objetosc - 50
    indeks_parametrow = zbuduj_indeks_parametrow(parametry)

    jony = []
    for p in lista_parametrow:
        parametr_key = znajdz_parametr(p, parametry, indeks_parametrow)
        if parametr_key and parametry[parametr_key]["jon"] == 1:
            jony.append(parametr_key)

    liczba_jonow = len(jony)

    if liczba_jonow > 0 and robocza >= 20:
        robocza -= 20
        jonogram_mozliwy = True
    else:
        jonogram_mozliwy = False

    param_ul = [
        get_adjusted_volume(
            parametry[parametr_key]["ul"],
            parametr_key,
            hemolysis,
            lipemia,
            icterus,
        )
        for p in lista_parametrow
        for parametr_key in [znajdz_parametr(p, parametry, indeks_parametrow)]
        if parametr_key and parametry[parametr_key]["jon"] == 0
    ]

    if robocza <= 0 or not param_ul:
        return (0,0)

    # MAX (od najmniejszych)
    suma = 0
    max_badan = 0

    for ul in sorted(param_ul):

        if suma + ul > robocza:
            break

        suma += ul
        max_badan += 1

    # MIN (od największych)
    suma = 0
    min_badan = 0

    for ul in sorted(param_ul, reverse=True):

        if suma + ul > robocza:
            break

        suma += ul
        min_badan += 1

    if jonogram_mozliwy:
        min_badan += liczba_jonow
        max_badan += liczba_jonow

    return (min_badan, max_badan)