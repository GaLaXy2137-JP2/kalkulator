import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
import json
#from silnik.db import connection_pool
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form  
from fastapi.responses import HTMLResponse  
from fastapi.templating import Jinja2Templates  
from fastapi.staticfiles import StaticFiles  
from silnik.liczenie_ceny import (  
    oblicz_cene,  
    wczytaj_profile_parametry,  
    wczytaj_profile_morfologia,
    wczytaj_parametry,
    wczytaj_ceny_profili,
    wczytaj_ceny_morfologii  
)  
import csv  
import psycopg2
ENV_PATH = Path(__file__).resolve().parent / ".env"
DOTENV_LOADED = load_dotenv(dotenv_path=ENV_PATH)
print(f"[app.py] .env loaded: {DOTENV_LOADED} | path: {ENV_PATH}")
print(f"[app.py] DATABASE_URL loaded: {bool(os.getenv('DATABASE_URL'))}")

from silnik.db import zapisz_historia_db

  
# =========================  
# SILNIKI  
# =========================  
  
from silnik.kalkulator import (  
    odmien_badanie,  
    objetosc_pelnego_profilu,  
    licz_zakres_excel,  
    zbuduj_liste_parametrow  
)  
  
from silnik.rozcienczenia import policz_rozcienczenia  
from silnik.db import zapisz_historia_db  
  
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
  
with open(BASE_DIR / "parametry.csv", newline="", encoding="utf-8-sig") as f:  
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
  
with open(BASE_DIR / "profile.csv", newline="", encoding="utf-8-sig") as f:  
    reader = csv.DictReader(f)  
  
    for r in reader:  
        profil = r["Profil"].strip()  
        parametr = r["Parametr"].strip()  
  
        if profil not in profile:  
            profile[profil] = []  
  
        profile[profil].append(parametr)  

# =========================
# WCZYTANIE CEN
# =========================

ceny_parametrow = {}

with open(BASE_DIR / "parametry_ceny.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for r in reader:
        nazwa = r["parametr"].strip()

        try:
            cena = float(r["dodaj"])
            ceny_parametrow[nazwa] = cena
        except:
            continue
  
# =========================  
# LISTA PROFILI  
# =========================  
  
def lista_profili():  
    return sorted(profile.keys())  
  
def lista_parametrow():  
    return sorted(parametry.keys())  


def parse_json_field(value, default):
    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    return default
  
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
  
def policz(objetosc, profil1, profil2, parametry_wybrane):  
  
    lista = zbuduj_liste_parametrow(  
        profil1,  
        profil2,  
        parametry_wybrane,  
        profile  
    )  
  
    if not lista:  
        return {  
            "komunikat": "Brak wybranych parametrów"  
        }  
  
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

    # 🔥 PARAMETRY Z URL
    parametry_qs = request.query_params.get("parametry")

    if parametry_qs:
        try:
            parametry_wybrane = json.loads(parametry_qs)
        except:
            parametry_wybrane = []
    else:
        parametry_wybrane = []

    wynik = None

    if objetosc:
        try:
            objetosc_int = int(objetosc)
            wynik = policz(objetosc_int, profil1, profil2, parametry_wybrane)
        except:
            wynik = None

    # ✅ TO MUSI BYĆ W ŚRODKU FUNKCJI
    return templates.TemplateResponse(
        request=request,
        name="kalkulator.html",
        context={
            "request": request,
            "profile": lista_profili(),
            "profile_param_map": profile,
            "parametry_lista": lista_parametrow(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2,
            "parametry_wybrane": parametry_wybrane,
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
    profil2: str = Form(""),  
    parametry_input: str = Form("")  
):  
  
    if parametry_input:  
        parametry_wybrane = [p.strip() for p in parametry_input.split(",")]  
    else:  
        parametry_wybrane = []  
  
    wynik = policz(objetosc, profil1, profil2, parametry_wybrane)  
  
    zapisz_historia_db(
    "kalkulator",
    objetosc,
    profil1,
    profil2,
    parametry_wybrane
) 
  
    return templates.TemplateResponse(  
        request=request,
        name="kalkulator.html",  
        context={  
            "request": request,  
            "profile": lista_profili(),  
            "profile_param_map": profile,
            "parametry_lista": lista_parametrow(),  
            "wynik": wynik,  
            "objetosc": objetosc,  
            "profil1": profil1,  
            "profil2": profil2, 
	    "parametry_wybrane": parametry_wybrane 
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

    # 🔥 PARAMETRY Z URL
    parametry_qs = request.query_params.get("parametry")

    if parametry_qs:
        try:
            parametry_wybrane = json.loads(parametry_qs)
        except:
            parametry_wybrane = []
    else:
        parametry_wybrane = []

    wynik = None

    if objetosc:
        try:
            objetosc_int = int(objetosc)

            lista = list(dict.fromkeys(
                parametry_z_profili(profil1, profil2) + parametry_wybrane
            ))

            wynik = policz_rozcienczenia(
                objetosc_int,
                lista,
                parametry
            )
        except:
            wynik = None

    return templates.TemplateResponse(
        request=request,
        name="rozcienczenia.html",
        context={
            "request": request,
            "profile": lista_profili(),
            "profile_param_map": profile,
            "parametry_lista": lista_parametrow(),
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2,
            "parametry_wybrane": parametry_wybrane  # 🔥 KLUCZ
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
    profil2: str = Form(""),
    parametry_input: str = Form("")  # 🔥 DODAJ TO
):

    # 🔥 parsowanie parametrów
    if parametry_input:
        parametry_wybrane = [p.strip() for p in parametry_input.split(",")]
    else:
        parametry_wybrane = []

    # 🔥 połączenie profili + klikniętych parametrów
    lista = list(dict.fromkeys(
        parametry_z_profili(profil1, profil2) + parametry_wybrane
    ))

    wynik = policz_rozcienczenia(
        objetosc,
        lista,
        parametry
    )

    zapisz_historia_db(
    "rozcienczenia",
    objetosc,
    profil1,
    profil2,
    parametry_wybrane
)

    return templates.TemplateResponse(
        request=request,
        name="rozcienczenia.html",
        context={
            "request": request,
            "profile": lista_profili(),
            "profile_param_map": profile,
            "parametry_lista": lista_parametrow(),  # 🔥 popraw też to
            "wynik": wynik,
            "objetosc": objetosc,
            "profil1": profil1,
            "profil2": profil2,
	    "parametry_wybrane": parametry_wybrane
        }
    )
# =========================
# STRONA HISTORII
# =========================

@app.get("/historia", response_class=HTMLResponse)
def historia(request: Request):
    from silnik.db import connection_pool
    import traceback

    conn = None
    cur = None

    try:
        conn = connection_pool.getconn()
        cur = conn.cursor()

        cur.execute("""
            SELECT data, godzina, modul, objetosc, profil1, profil2, parametry, wynik
            FROM historia
            ORDER BY data DESC
            LIMIT 100
        """)

        rows = cur.fetchall()
        dane = []

        for r in rows:
            try:
                parametry_value = r[6]
                wynik_value = r[7]

                try:
                    if isinstance(parametry_value, str):
                        parametry_value = json.loads(parametry_value)
                except Exception:
                    pass

                try:
                    if isinstance(wynik_value, str):
                        wynik_value = json.loads(wynik_value)
                except Exception:
                    pass

                dane.append({
                    "data": str(r[0]),
                    from datetime import datetime
                    "godzina": str(r[1])[:5] if r[1] else "",
                    "modul": r[2],
                    "objetosc": r[3],
                    "profil1": r[4],
                    "profil2": r[5],
                    "parametry": parametry_value if parametry_value is not None else [],
                    "wynik": wynik_value if wynik_value is not None else {}
                })

            except Exception as row_error:
                print(f"[historia] row parse error: {type(row_error).__name__}: {row_error}")
                print(traceback.format_exc())

                dane.append({
                    "data": str(r[0]) if len(r) > 0 else "",
                    "godzina": str(r[1])[:5] if len(r) > 1 and r[1] else "",
                    "modul": r[2] if len(r) > 2 else "",
                    "objetosc": r[3] if len(r) > 3 else "",
                    "profil1": r[4] if len(r) > 4 else "",
                    "profil2": r[5] if len(r) > 5 else "",
                    "parametry": r[6] if len(r) > 6 else [],
                    "wynik": r[7] if len(r) > 7 else {}
                })

        return templates.TemplateResponse(
            request=request,
            name="historia.html",
            context={
                "request": request,
                "historia": dane
            }
        )

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[historia] ERROR: {type(e).__name__}: {e}")
        print(tb)

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Historia - Debug</title></head>
                <body style="font-family: monospace; white-space: pre-wrap; padding: 20px;">
                    <h2>Blad w /historia</h2>
                    <b>{type(e).__name__}: {e}</b>

{tb}
                </body>
            </html>
            """,
            status_code=500
        )

    finally:
        if cur:
            cur.close()
        if conn:
            connection_pool.putconn(conn)
# =========================
# STRONA CEN
# =========================

def lista_profili_ceny():
    profile_param = wczytaj_profile_parametry()
    return sorted(profile_param.keys())


@app.get("/ceny", response_class=HTMLResponse)
def ceny(request: Request):

    profil = request.query_params.get("profil")
    morfologia = request.query_params.get("morfologia", "brak")
    parametry_input = request.query_params.get("parametry")

    if parametry_input:
        wykonane = [p.strip() for p in parametry_input.split(",")]
    else:
        wykonane = []

    wynik = None
    sekcje = None
    ma_morfologie = False

    # 🔥 JEDYNE ŹRÓDŁO PARAMETRÓW (backend + frontend)
    parametry_ceny = wczytaj_parametry()

    # 🔥 cena profilu (do live JS)
    cena_profilu = 0

    if profil:

        profile_param = wczytaj_profile_parametry()
        profile_morf = wczytaj_profile_morfologia()
        ceny_profili = wczytaj_ceny_profili()
        ceny_morf = wczytaj_ceny_morfologii()

        lista = profile_param.get(profil, [])

        # 🔥 cena bazowa profilu
        cena_profilu = ceny_profili.get(profil, 0)

        # 🔥 dodanie morfologii do ceny
        if morfologia == "podstawowa":
            cena_profilu += ceny_morf.get("podstawowa", 0)

        if morfologia == "rozszerzona":
            cena_profilu += ceny_morf.get("rozszerzona", 0)

        # czy profil ma morfologię
        ma_morfologie = profile_morf.get(profil, 0) == 1
        print("PARAMETRY CENY:", parametry_ceny)
        print("WYKONANE:", wykonane)
        # =========================
        # PODZIAŁ NA SEKCJE
        # =========================

        sekcje = {
            "biochemia": [],
            "mocz": []
        }

        BADANIA_MOCZU = [
            "Stosunek; białko / kreatynina w moczu",
            "Badanie osadu moczu",
            "Badanie moczu podstawowe"
        ]

        for p in lista:
            if p in BADANIA_MOCZU:
                sekcje["mocz"].append(p)
            else:
                sekcje["biochemia"].append(p)

        # =========================
        # LICZENIE (backend)
        # =========================

        if "oblicz" in request.query_params:
            wynik = oblicz_cene(profil, wykonane, morfologia)
            if "oblicz" in request.query_params:
                zapisz_historia_db(
                    "ceny",
                    0,
                    profil,
                    "",
                    wykonane,
                    wynik,
                    morfologia
                )
    return templates.TemplateResponse(
        request=request,
        name="ceny.html",
        context={
            "request": request,
            "profile": lista_profili_ceny(),
            "wybrany_profil": profil,
            "sekcje": sekcje,
            "wynik": wynik,
            "morfologia": morfologia,
            "ma_morfologie": ma_morfologie,
            "wykonane": wykonane,

            # 🔥 KLUCZOWE
            "parametry_ceny": parametry_ceny,
            "cena_profilu": cena_profilu,
        }
    )