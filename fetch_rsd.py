# fetch_rsd.py
import os
from datetime import datetime, timezone
from pathlib import Path
import requests

RSD_URL = os.getenv("RSD_URL", "https://cloud.ostrava.cz/public.php/webdav/upload.xml")
RSD_USERNAME = os.getenv("RSD_USERNAME")  # nastav v GitHub Secrets
RSD_PASSWORD = os.getenv("RSD_PASSWORD")  # nastav v GitHub Secrets
OUT_DIR = Path(os.getenv("OUT_DIR", "data"))

def main():
    if not RSD_USERNAME or not RSD_PASSWORD:
        raise RuntimeError("Chybí RSD_USERNAME/RSD_PASSWORD v proměnných prostředí.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # čas v UTC (stabilní pro názvy souborů)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"upload_{ts}.xml"

    resp = requests.get(
        RSD_URL,
        auth=(RSD_USERNAME, RSD_PASSWORD),
        headers={"Accept": "application/xml"},
        timeout=60,
    )
    resp.raise_for_status()

    out_path.write_bytes(resp.content)
    print(f"Saved snapshot: {out_path} ({len(resp.content)} bytes)")

if __name__ == "__main__":
    main()
