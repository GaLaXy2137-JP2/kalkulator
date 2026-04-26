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

from silnik.db import connection_pool, pobierz_kolumny_historia, zapisz_historia_db, zbuduj_select_historii

  
# =========================  
# SILNIKI  
# =========================  
  
from silnik.kalkulator import (  
    odmien_badanie,  
    objetosc_pelnego_profilu,  
    rozbij_objetosc_pelnego_profilu,
    licz_zakres_excel,  
    zbuduj_liste_parametrow  
)  
  
from silnik.rozcienczenia import policz_rozcienczenia  
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


def pobierz_hil_z_query(request: Request):
    return {
        "hemolysis": request.query_params.get("hemolysis", "none"),
        "lipemia": request.query_params.get("lipemia", "none"),
        "icterus": request.query_params.get("icterus", "absent"),
    }


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
  
def policz(objetosc, profil1, profil2, parametry_wybrane, hemolysis="none", lipemia="none", icterus="absent"):  
  
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
  
    potrzebne_breakdown = rozbij_objetosc_pelnego_profilu(lista, parametry, hemolysis, lipemia, icterus)
    potrzebne = potrzebne_breakdown["suma"]

    wynik_potrzebne = {
        "potrzebne_ul": potrzebne,
        "potrzebne_martwa_objetosc_ul": potrzebne_breakdown["martwa_objetosc_ul"],
        "potrzebne_jonogram_ul": potrzebne_breakdown["jonogram_ul"],
        "potrzebne_parametry_ul": potrzebne_breakdown["parametry_ul"],
    }
  
    if objetosc <= 60:  
        return {  
            "komunikat": "Za mało próbki – anuluj profil",  
            **wynik_potrzebne,
        }  
  
    if objetosc >= potrzebne:  
        return {  
            "komunikat": "Materiał wystarczający na cały profil",  
            **wynik_potrzebne,
        }  
  
    min_g, max_g = licz_zakres_excel(objetosc, lista, parametry, hemolysis, lipemia, icterus)  
  
    lista_bez = [p for p in lista if p != "GLDH"]  
  
    min_b, max_b = licz_zakres_excel(objetosc, lista_bez, parametry, hemolysis, lipemia, icterus)  
  
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
            **wynik_potrzebne,
        }  
    else:  
        return {  
            "bez_gldh": f"{min_b}-{max_b}",  
            "sr_bez_gldh": f"{sr_b} {forma_b}",  
            **wynik_potrzebne,
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

    hil = pobierz_hil_z_query(request)

    wynik = None

    if objetosc:
        try:
            objetosc_int = int(objetosc)
            wynik = policz(
                objetosc_int,
                profil1,
                profil2,
                parametry_wybrane,
                hil["hemolysis"],
                hil["lipemia"],
                hil["icterus"],
            )
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
            "hemolysis": hil["hemolysis"],
            "lipemia": hil["lipemia"],
            "icterus": hil["icterus"],
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
    parametry_input: str = Form(""),
    hemolysis: str = Form("none"),
    lipemia: str = Form("none"),
    icterus: str = Form("absent"),
):  
  
    if parametry_input:  
        parametry_wybrane = [p.strip() for p in parametry_input.split(",")]  
    else:  
        parametry_wybrane = []  
  
    wynik = policz(objetosc, profil1, profil2, parametry_wybrane, hemolysis, lipemia, icterus)  
  
    zapisz_historia_db(
    "kalkulator",
    objetosc,
    profil1,
    profil2,
    parametry_wybrane,
    wynik,
    hemolysis=hemolysis,
    lipemia=lipemia,
    icterus=icterus,
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
	    "parametry_wybrane": parametry_wybrane,
            "hemolysis": hemolysis,
            "lipemia": lipemia,
            "icterus": icterus,
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

    hil = pobierz_hil_z_query(request)

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
                parametry,
                hil["hemolysis"],
                hil["lipemia"],
                hil["icterus"],
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
            "parametry_wybrane": parametry_wybrane,
            "hemolysis": hil["hemolysis"],
            "lipemia": hil["lipemia"],
            "icterus": hil["icterus"],
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
    parametry_input: str = Form(""),
    hemolysis: str = Form("none"),
    lipemia: str = Form("none"),
    icterus: str = Form("absent"),
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
        parametry,
        hemolysis,
        lipemia,
        icterus,
    )

    zapisz_historia_db(
    "rozcienczenia",
    objetosc,
    profil1,
    profil2,
    parametry_wybrane,
    wynik,
    hemolysis=hemolysis,
    lipemia=lipemia,
    icterus=icterus,
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
	    "parametry_wybrane": parametry_wybrane,
            "hemolysis": hemolysis,
            "lipemia": lipemia,
            "icterus": icterus,
        }
    )
# =========================
# STRONA HISTORII
# =========================

@app.get("/historia", response_class=HTMLResponse)
def historia(request: Request):
    conn = None
    cur = None

    try:
        conn = connection_pool.getconn()
        cur = conn.cursor()

        dostepne_kolumny = pobierz_kolumny_historia(cur)
        cur.execute(zbuduj_select_historii(dostepne_kolumny))

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

                hil_meta = {}
                if isinstance(wynik_value, dict):
                    hil_meta = wynik_value.pop("_hil", {}) or {}

                dane.append({
                    "data": str(r[0]),
                    "godzina": str(r[1])[:5] if r[1] else "",
                    "modul": r[2],
                    "objetosc": r[3],
                    "profil1": r[4],
                    "profil2": r[5],
                    "parametry": parametry_value if parametry_value is not None else [],
                    "wynik": wynik_value if wynik_value is not None else {},
                    "hemolysis": r[8] if len(r) > 8 and r[8] is not None else hil_meta.get("hemolysis", ""),
                    "lipemia": r[9] if len(r) > 9 and r[9] is not None else hil_meta.get("lipemia", ""),
                    "icterus": r[10] if len(r) > 10 and r[10] is not None else hil_meta.get("icterus", ""),
                })

            except Exception as row_error:
                print(f"[historia] row parse error: {type(row_error).__name__}: {row_error}")

                dane.append({
                    "data": str(r[0]) if len(r) > 0 else "",
                    "godzina": str(r[1])[:5] if len(r) > 1 and r[1] else "",
                    "modul": r[2] if len(r) > 2 else "",
                    "objetosc": r[3] if len(r) > 3 else "",
                    "profil1": r[4] if len(r) > 4 else "",
                    "profil2": r[5] if len(r) > 5 else "",
                    "parametry": r[6] if len(r) > 6 else [],
                    "wynik": r[7] if len(r) > 7 else {},
                    "hemolysis": r[8] if len(r) > 8 and r[8] is not None else "",
                    "lipemia": r[9] if len(r) > 9 and r[9] is not None else "",
                    "icterus": r[10] if len(r) > 10 and r[10] is not None else "",
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
        print(f"[historia] ERROR: {type(e).__name__}: {e}")

        return HTMLResponse(
            content="Wystąpił błąd serwera",
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


@app.api_route("/ceny", methods=["GET", "POST"], response_class=HTMLResponse)
async def ceny(request: Request):

    profile_param = wczytaj_profile_parametry()
    profile_morf = wczytaj_profile_morfologia()
    ceny_profili = wczytaj_ceny_profili()
    ceny_morf = wczytaj_ceny_morfologii()
    parametry_ceny = wczytaj_parametry()

    profil = ""
    morfologia = "brak"
    wykonane = []
    wynik = None
    zapisano = False

    if request.method == "POST":
        form = await request.form()
        profil = (form.get("profil") or "").strip()
        morfologia = (form.get("morfologia") or "brak").strip() or "brak"
        wykonane = parse_json_field(form.get("wykonane_json"), [])
        akcja = (form.get("action") or "").strip()
    else:
        profil = (request.query_params.get("profil") or "").strip()
        morfologia = (request.query_params.get("morfologia") or "brak").strip() or "brak"
        wykonane = parse_json_field(request.query_params.get("wykonane_json"), [])

        if not wykonane:
            parametry_input = request.query_params.get("parametry")
            if parametry_input:
                wykonane = [p.strip() for p in parametry_input.split(",") if p.strip()]

        akcja = ""

    if not isinstance(wykonane, list):
        wykonane = []

    wykonane = [str(p).strip() for p in wykonane if str(p).strip()]
    wykonane = list(dict.fromkeys(wykonane))

    ma_morfologie = profile_morf.get(profil, 0) == 1 if profil else False

    if not ma_morfologie:
        morfologia = "brak"

    if profil:
        wynik = oblicz_cene(profil, wykonane, morfologia)

        if request.method == "POST" and akcja == "save" and wynik:
            zapisz_historia_db(
                "ceny",
                0,
                profil,
                "",
                wykonane,
                wynik,
                morfologia
            )
            zapisano = True

    return templates.TemplateResponse(
        request=request,
        name="ceny.html",
        context={
            "request": request,
            "profile": lista_profili_ceny(),
            "wybrany_profil": profil,
            "wynik": wynik,
            "morfologia": morfologia,
            "ma_morfologie": ma_morfologie,
            "wykonane": wykonane,
            "parametry_ceny": parametry_ceny,
            "profile_param_map": profile_param,
            "profile_morf_map": profile_morf,
            "ceny_profili_map": ceny_profili,
            "ceny_morf_map": ceny_morf,
            "zapisano": zapisano,
        }
    )