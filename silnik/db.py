import os
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

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

        now = datetime.now(ZoneInfo("Europe/Warsaw"))
        data = now.date()
        godzina = now.time().replace(tzinfo=None, microsecond=0)

        parametry_json = json.dumps(parametry) if parametry else json.dumps([])
        wynik_json = json.dumps(wynik) if wynik else json.dumps({})

        try:
            cur.execute("""
                INSERT INTO historia
                (data, godzina, modul, objetosc, profil1, profil2, parametry, wynik, hemolysys, lipemia, icterus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data,
                godzina,
                modul,
                objetosc,
                profil1,
                profil2,
                parametry_json,
                wynik_json,
                hemolysis,
                lipemia,
                icterus,
            ))
        except psycopg2.errors.UndefinedColumn:
            conn.rollback()
            cur = conn.cursor()

            legacy_wynik = wynik if isinstance(wynik, dict) else ({} if wynik is None else {"value": wynik})
            if hemolysis or lipemia or icterus:
                legacy_wynik["_hil"] = {
                    "hemolysis": hemolysis or "",
                    "lipemia": lipemia or "",
                    "icterus": icterus or "",
                }

            cur.execute("""
                INSERT INTO historia
                (data, godzina, modul, objetosc, profil1, profil2, parametry, wynik)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data,
                godzina,
                modul,
                objetosc,
                profil1,
                profil2,
                parametry_json,
                json.dumps(legacy_wynik),
            ))

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