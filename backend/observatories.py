import json
from pathlib import Path
from astropy.coordinates import EarthLocation

OBSERVATORIES_CACHE_FILE = Path(__file__).parent / "observatories.json"

def build_observatories_cache():
    site_names = EarthLocation.get_site_names()
    observatories = []
    seen = set()

    for name in site_names:
        if name in seen or not name:
            continue
        seen.add(name)
        try:
            loc = EarthLocation.of_site(name)
            observatories.append({
                "name": name,
                "lat": loc.lat.deg,
                "lon": loc.lon.deg,
            })
        except Exception:
            continue

    return observatories

def get_observatories(force_refresh: bool = False):
    if not force_refresh and OBSERVATORIES_CACHE_FILE.exists():
        with open (OBSERVATORIES_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    observatories = build_observatories_cache()

    with open(OBSERVATORIES_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(observatories, f, indent=2, ensure_ascii=False)


    return observatories