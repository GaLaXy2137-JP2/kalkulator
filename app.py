from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import csv

# =========================
# SILNIKI
# =========================

from silnik.kalkulator import odmien_badanie, objetosc_pelnego_profilu, licz_zakres_excel
from silnik.rozcienczenia import policz_rozcienczenia
from silnik.historia import zapisz_historia

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# =========================
# DANE
# =========================

parametry = {}
profile = {}

# =========================
# WCZYTANIE PARAMETRÓW
# =========================

with open("parametry.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for r in reader:
        nazwa = r["Parametr"].strip()

        parametry[nazwa] = {
            "ul": float(r["Olimpus B"]),
            "jon": int(r["Czy jon"]),
            "rozc": int(r["Czy rozcienczalne"])
        }

# =========================
# WCZYTANIE PROFILI
# =========================

with open("profile.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for r in reader:
        profil = r["Profil"].strip()
        parametr = r["Parametr"].strip()

        if profil not in profile:
            profile[profil] = []

        profile[profil].append(parametr)

# =========================
# LISTA PROFILI
# =========================

def lista_profili():
    return sorted(profile.keys())

# =========================
# PARAMETRY Z PROFILI
# =========================

def parametry_z_profili(profil1, profil2):

    lista = []

    if profil1 in profile:
        lista += profile[profil1]

    if profil2 in profile:
        lista += profile[profil2]

    return list(dict.fromkeys(lista))

# =========================
# LOGIKA KALKULATORA
# =========================

def policz(objetosc, profil1, profil2):

    lista = parametry_z_profili(profil1, profil2)

    potrzebne = objetosc_pelnego_profilu(lista, parametry)

    if objetosc < 60:
        return {
            "komunikat": "Za mało próbki – anuluj profil",
            "potrzebne_ul": potrzebne
        }

    if objetosc >= potrzebne:
        return {
            "komunikat": "Materiał wystarczający na cały profil",
            "potrzebne_ul": potrzebne
        }

    min_g, max_g = licz_zakres_excel(objetosc, lista, parametry)

    lista_bez = [p for p in lista if p != "GLDH"]

    min_b, max_b = licz_zakres_excel(objetosc, lista_bez, parametry)

    sr_g = int((min_g + max_g) / 2)
    sr_b = int((min_b + max_b) / 2)

    forma_g = odmien_badanie(sr_g)
    forma_b = odmien_badanie(sr_b)

    if "GLDH" in lista:
        return {
            "z_gldh": f"{min_g}-{max_g}",
            "bez_gldh": f"{min_b}-{max_b}",
            "sr_z_gldh": f"{sr_g} {forma_g}",
            "sr_bez_gldh": f"{sr_b} {forma_b}",
            "potrzebne_ul": potrzebne
        }
    else:
        return {
            "bez_gldh": f"{min_b}-{max_b}",
            "sr_bez_gldh": f"{sr_b} {forma_b}",
            "potrzebne_ul": potrzebne
        }

# =========================
# STRONA KALKULATORA
# =========================

@app.get("/", response_class=HTMLResponse)
def strona(request: Request):

    objetosc = request.query_params.get("objetosc")
    profil1 = request.query_params.get("profil1")
    profil2 = request.query_params.get("profil2")

    wynik = None

    if objetosc:
        try:
            objetosc_int = int(objetosc)
            wynik = policz(objetosc_int, profil1, profil2)
        except:
            wynik = None

    return templates.TemplateResponse(
        "kalkulator.html",
        {
            "request": request,
            "profile": lista_profili(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2
        }
    )

# =========================
# OBLICZENIE KALKULATORA
# =========================

@app.post("/", response_class=HTMLResponse)
def oblicz(
    request: Request,
    objetosc: int = Form(...),
    profil1: str = Form(""),
    profil2: str = Form("")
):

    wynik = policz(objetosc, profil1, profil2)

    zapisz_historia("kalkulator", objetosc, profil1, profil2)

    return templates.TemplateResponse(
        "kalkulator.html",
        {
            "request": request,
            "profile": lista_profili(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2
        }
    )

# =========================
# STRONA ROZCIEŃCZEŃ
# =========================

@app.get("/rozcienczenia", response_class=HTMLResponse)
def rozcienczenia_strona(request: Request):

    objetosc = request.query_params.get("objetosc")
    profil1 = request.query_params.get("profil1")
    profil2 = request.query_params.get("profil2")

    wynik = None

    if objetosc:
        try:
            objetosc_int = int(objetosc)

            lista = parametry_z_profili(profil1, profil2)

            wynik = policz_rozcienczenia(
                objetosc_int,
                lista,
                parametry
            )
        except:
            wynik = None

    return templates.TemplateResponse(
        "rozcienczenia.html",
        {
            "request": request,
            "profile": lista_profili(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2
        }
    )

# =========================
# OBLICZENIE ROZCIEŃCZEŃ
# =========================

@app.post("/rozcienczenia", response_class=HTMLResponse)
def oblicz_rozcienczenia(
    request: Request,
    objetosc: int = Form(...),
    profil1: str = Form(""),
    profil2: str = Form("")
):

    lista = parametry_z_profili(profil1, profil2)

    wynik = policz_rozcienczenia(
        objetosc,
        lista,
        parametry
    )

    zapisz_historia("rozcienczenia", objetosc, profil1, profil2)

    return templates.TemplateResponse(
        "rozcienczenia.html",
        {
            "request": request,
            "profile": lista_profili(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2
        }
    )

# =========================
# STRONA HISTORII
# =========================

@app.get("/historia", response_class=HTMLResponse)
def historia(request: Request):

    dane = []

    try:
        with open("historia.csv", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                dane.append(r)
    except:
        dane = []

    dane.reverse()

    return templates.TemplateResponse(
        "historia.html",
        {
            "request": request,
            "historia": dane
        }
    )