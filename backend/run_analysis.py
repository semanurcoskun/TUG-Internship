import numpy as np
import json
from astropy.coordinates import EarthLocation
from calculations import get_time_sequence, compute_target_metrics
from weather_service import get_hourly_weather, match_weather_to_time_sequence
from scoring import evaluate_target, calculate_score
from astropy.utils.exceptions import AstropyWarning
import warnings
import asyncio
warnings.simplefilter('ignore', category=AstropyWarning)  # Ignore Astropy warnings for cleaner output

async def run_analysis():
    tug = EarthLocation.of_site("TUG")
    obs_date_str = "2026-08-09 12:00:00"

    time_sequence = get_time_sequence(obs_date_str, tug)

    start_date = time_sequence[0].datetime.strftime("%Y-%m-%d")
    end_date = time_sequence[-1].datetime.strftime("%Y-%m-%d")

    weather_df = await get_hourly_weather(tug, start_date, end_date)
    weather = match_weather_to_time_sequence(weather_df, time_sequence)


    with open("targets.json", "r", encoding="utf-8") as f:
        targets = json.load(f)

    results = []
    for target in targets:
        metrics = compute_target_metrics(target, tug, time_sequence)
        result = evaluate_target(target, metrics, weather, time_sequence)
        results.append(result)

    observable = [r for r in results if r["observable"]]
    observable.sort(key=lambda r: r["score"], reverse=True)

    print(f"\n{len(observable)}/{len(results)} target could be observed\n")
    for r in results:
        if r["observable"]:
            continuity = "continuous" if r["window_is_continuous"] else "discontinuous"
            print(f"{r['name']:<10} -> Observable: {r['window_start_utc']} to {r['window_end_utc']}")
            print(f"{' '*13} Best Time : {r['best_time_utc']}, Observable Minutes: {r['observable_minutes']} ({continuity})")
            print(f"{' '*13} Metrics   : Alt: {r['best_altitude']}° | Airmass: {r['best_airmass']}")
                
            print(f"{' '*13} Moon Info : Sep: {r['moon_separation_deg']}° | Illum: {r['moon_illumination']}")
            print(f"{' '*13} Weather   : Cloud: {r['cloud_cover']}% | Temperature: {r['temperature_2m']}°C | Wind: {r['wind_speed_10m']} km/h | Humidity: {r['relative_humidity_2m']}%")
            print("-" * 65)
        else:
            print(f"{r['name']:<10} -> Not observable.")
            print("-" * 65) 

if __name__ == "__main__":
    asyncio.run(run_analysis())