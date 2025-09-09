# fetch_rsd.py
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RSD_URL = os.getenv("RSD_URL", "https://cloud.ostrava.cz/public.php/webdav/upload.xml")
RSD_USERNAME = os.getenv("RSD_USERNAME")
RSD_PASSWORD = os.getenv("RSD_PASSWORD")
OUT_DIR = Path(os.getenv("OUT_DIR", "data"))

# SOFT_FAIL=true -> při dočasném selhání neskončí job chybou
SOFT_FAIL = os.getenv("SOFT_FAIL", "true").lower() in ("1", "true", "yes")

def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,              # max 5 pokusů
        read=5,
        connect=5,
        backoff_factor=1.5,   # exponenciální prodleva
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({
        "Accept": "application/xml",
        "User-Agent": "RSD-Snapshot/1.0 (+GitHub Actions)",
        "Connection": "keep-alive",
    })
    return s

def main():
    if not RSD_USERNAME or not RSD_PASSWORD:
        raise RuntimeError("Chybí RSD_USERNAME/RSD_PASSWORD v proměnných prostředí.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"upload_{ts}.xml"

    session = make_session()
    try:
        # timeout=(connect, read) – prodloužené čtení pro pomalejší server
        resp = session.get(
            RSD_URL,
            auth=(RSD_USERNAME, RSD_PASSWORD),
            timeout=(15, 180),
            stream=True,
        )
        resp.raise_for_status()

        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)

        if out_path.stat().st_size == 0:
            raise RuntimeError("Stažený soubor má nulovou velikost.")

        with open(out_path, "rb") as f:
            head = f.read(64).lstrip()
            if not head.startswith(b"<"):
                print(f"Upozornění: začátek souboru nevypadá jako XML: {head[:16]!r}")

        print(f"Saved snapshot: {out_path} ({out_path.stat().st_size} bytes)")

    except Exception as e:
        msg = f"[WARN] Snapshot se nepodařilo stáhnout: {e}"
        if SOFT_FAIL:
            print(msg, file=sys.stderr)
            return
        else:
            raise

if __name__ == "__main__":
    main()
