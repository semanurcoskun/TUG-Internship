from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u
from astroplan import Observer
import numpy as np
import json
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from astropy.coordinates import get_body
from astroplan import moon_illumination
from astropy.utils.exceptions import AstropyWarning
import warnings
warnings.simplefilter('ignore', category=AstropyWarning)  # Ignore Astropy warnings for cleaner output


tug = EarthLocation.of_site("TUG")

observer = Observer(location = tug, name ="TUG")
obs_date = Time("2026-08-07 12:00:00", scale = "utc")
sunset = observer.sun_set_time(obs_date, which="next") 
sunrise = observer.sun_rise_time(sunset, which="next")
period = np.linspace(sunset.jd, sunrise.jd, 60)
sequence = Time(period, format="jd")

tf = TimezoneFinder()
tz_string = tf.timezone_at(lng=tug.lon.deg, lat=tug.lat.deg)
local_tz = ZoneInfo(tz_string) if tz_string else ZoneInfo("UTC")

MAX_AIRMASS = 2.0
MOON_ILLUM_REJECT = 0.85 #ay yüzde 85ten daha görünürse ele
MOON_SEP_MIN_DEG = 30.0 #hedef aya 30 derecenin altında yakınsa

def analyze_target(target_dict, location, time_sequence , min_alt, max_alt):
    coord = SkyCoord(
    ra = float(target_dict["ra"]) * u.deg,
    dec = float(target_dict["dec"]) * u.deg,
    unit = (u.deg, u.deg),
    frame = "icrs",
    )

    altaz_frame = AltAz(obstime=time_sequence, location=location)
    target_altaz = coord.transform_to(altaz_frame)

    heights = target_altaz.alt.deg
    airmasses = target_altaz.secz

    moon_pos = get_body("moon", time_sequence, location=tug)
    moon_sep = coord.separation(moon_pos).deg
    illum = moon_illumination(time_sequence)

    can_observe = (
        (heights >= min_alt) & (heights <= max_alt)
        & (airmasses <= MAX_AIRMASS)
        & (moon_sep >= MOON_SEP_MIN_DEG)
        & (illum <= MOON_ILLUM_REJECT)
    )
    result = {
        "id": target_dict["id"],
        "name": target_dict["name"],
        "observable": bool(can_observe.any()),
        "observable_minutes": int(can_observe.sum()),
    }

    if can_observe.any():
        
        valid_airmasses = np.where(can_observe, airmasses, np.inf) #returns airmass values where can_observe is True, otherwise returns np.inf
        best_index = np.argmin(valid_airmasses) #returns the index of the minimum value in valid_airmasses, which corresponds to the best airmass during the observable period

        window_times = time_sequence[can_observe]

        result["window_start_utc"] = window_times[0].iso[:16]
        result["window_end_utc"] = window_times[-1].iso[:16]
        result["best_time_utc"] = time_sequence[best_index].iso[:16]

        result["window_start_local"] = window_times[0].to_datetime(timezone=local_tz).strftime("%Y-%m-%d %H:%M")
        result["window_end_local"] = window_times[-1].to_datetime(timezone=local_tz).strftime("%Y-%m-%d %H:%M")
        result["best_time_local"] = time_sequence[best_index].to_datetime(timezone=local_tz).strftime("%Y-%m-%d %H:%M")

        result["best_airmass"] = round(float(airmasses[best_index]), 2)
        result["best_altitude"] = round(float(heights[best_index]), 1)

        result["moon_separation_deg"] = round(float(moon_sep[best_index]), 1)
        result["moon_illumination"] = round(float(illum[best_index]), 2)

    return result

if __name__ == "__main__":
    with open("targets.json", "r", encoding="utf-8") as f:
        targets = json.load(f)

    results = []
    for target in targets:
        result = analyze_target(target, tug, sequence, min_alt=20, max_alt=80)
        results.append(result)

    for r in results:
            if r["observable"]:
                print(f"{r['name']:<10} -> Observable: {r['window_start_utc']} to {r['window_end_utc']}")
                print(f"{' '*13} Best Time : {r['best_time_utc']}")
                print(f"{' '*13} Metrics   : Alt: {r['best_altitude']}° | Airmass: {r['best_airmass']}")
                
                # Ay ayrıklığı ve parlaklığı formatlaması (örn: parlaklık ondalık ise düzgün gözükmesi için)
                # Eğer moon_illumination 0-1 arası bir değerse sonuna % eklemek için float yapısına sokabilirsin, 
                # ancak orijinal formatını korumak için doğrudan yazdırıyoruz:
                print(f"{' '*13} Moon Info : Sep: {r['moon_separation_deg']}° | Illum: {r['moon_illumination']}")
                print("-" * 65)
            else:
                print(f"{r['name']:<10} -> Not observable.")
                print("-" * 65) 
