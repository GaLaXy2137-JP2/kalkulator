import os
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from psycopg2 import pool
import psycopg2
from dotenv import load_dotenv

# =========================
# ENV
# =========================

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"[db.py] ENV path: {ENV_PATH}")
print(f"[db.py] DATABASE_URL loaded: {bool(DATABASE_URL)}")

# =========================
# CONNECTION POOL
# =========================

connection_pool = None

if DATABASE_URL:
    connection_pool = pool.SimpleConnectionPool(
        1, 10,
        DATABASE_URL
    )
    print("[db.py] Connection pool created")
else:
    print("[db.py] ERROR: DATABASE_URL missing")


def pobierz_kolumny_historia(cur):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'historia'
        """
    )
    return {row[0] for row in cur.fetchall()}


def mapuj_kolumny_hil(dostepne_kolumny):
    if "hemolysis" in dostepne_kolumny:
        hemolysis_column = "hemolysis"
    elif "hemolysys" in dostepne_kolumny:
        hemolysis_column = "hemolysys"
    else:
        hemolysis_column = None

    return {
        "hemolysis": hemolysis_column,
        "lipemia": "lipemia" if "lipemia" in dostepne_kolumny else None,
        "icterus": "icterus" if "icterus" in dostepne_kolumny else None,
    }


def dolacz_hil_do_wyniku(wynik, hemolysis=None, lipemia=None, icterus=None):
    if isinstance(wynik, dict):
        payload = dict(wynik)
    elif wynik is None:
        payload = {}
    else:
        payload = {"value": wynik}

    payload["_hil"] = {
        "hemolysis": hemolysis or "",
        "lipemia": lipemia or "",
        "icterus": icterus or "",
    }
    return payload


def zbuduj_select_historii(dostepne_kolumny):
    hil_kolumny = mapuj_kolumny_hil(dostepne_kolumny)

    select_hil = []
    for nazwa in ("hemolysis", "lipemia", "icterus"):
        kolumna = hil_kolumny[nazwa]
        if kolumna:
            select_hil.append(f"{kolumna} AS {nazwa}")
        else:
            select_hil.append(f"NULL AS {nazwa}")

    return """
        SELECT data, godzina, modul, objetosc, profil1, profil2, parametry, wynik, {hil_select}
        FROM historia
        ORDER BY data DESC, godzina DESC
        LIMIT 100
    """.format(hil_select=", ".join(select_hil))


def pobierz_biezacy_czas():
    try:
        return datetime.now(ZoneInfo("Europe/Warsaw"))
    except ZoneInfoNotFoundError:
        print("[db.py] WARNING: Europe/Warsaw timezone missing, using local system time")
        return datetime.now()


# =========================
# ZAPIS HISTORII
# =========================

def zapisz_historia_db(modul, objetosc, profil1, profil2, parametry, wynik=None, morfologia=None, hemolysis=None, lipemia=None, icterus=None):

    conn = None
    cur = None

    try:
        if not connection_pool:
            print("[db.py] ERROR: No connection pool")
            return

        # 🔥 zamiast connect()
        conn = connection_pool.getconn()
        cur = conn.cursor()

        now = pobierz_biezacy_czas()
        data = now.date()
        godzina = now.time().replace(tzinfo=None, microsecond=0)

        dostepne_kolumny = pobierz_kolumny_historia(cur)
        hil_kolumny = mapuj_kolumny_hil(dostepne_kolumny)

        parametry_json = json.dumps(parametry) if parametry else json.dumps([])
        brakuje_kolumn_hil = any(kolumna is None for kolumna in hil_kolumny.values())
        wynik_payload = dolacz_hil_do_wyniku(wynik, hemolysis, lipemia, icterus) if brakuje_kolumn_hil else (wynik if wynik else {})
        wynik_json = json.dumps(wynik_payload)

        kolumny = ["data", "godzina", "modul", "objetosc", "profil1", "profil2", "parametry", "wynik"]
        wartosci = [data, godzina, modul, objetosc, profil1, profil2, parametry_json, wynik_json]

        wartosci_hil = {
            "hemolysis": hemolysis,
            "lipemia": lipemia,
            "icterus": icterus,
        }

        for nazwa in ("hemolysis", "lipemia", "icterus"):
            kolumna = hil_kolumny[nazwa]
            if kolumna:
                kolumny.append(kolumna)
                wartosci.append(wartosci_hil[nazwa])

        placeholders = ", ".join(["%s"] * len(kolumny))
        cur.execute(
            f"""
                INSERT INTO historia
                ({", ".join(kolumny)})
                VALUES ({placeholders})
            """,
            tuple(wartosci),
        )

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[db.py] ERROR: {type(e).__name__}: {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            # 🔥 zamiast close()
            connection_pool.putconn(conn)