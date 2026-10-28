import numpy as np
import json
from astropy.coordinates import EarthLocation
from calculations import get_time_sequence, compute_target_metrics, get_moon_phase
from weather_service import get_hourly_weather, match_weather_to_time_sequence
from astropy.utils.exceptions import AstropyWarning
import warnings
import asyncio
warnings.simplefilter('ignore', category=AstropyWarning)  # Ignore Astropy warnings for cleaner output

MIN_ALT = 20
MAX_ALT = 80
MAX_AIRMASS = 2.0
MOON_ILLUM_REJECT = 0.85
MOON_SEP_MIN_DEG = 30.0
MAX_CLOUD_COVER = 70.0
MAX_WIND_SPEED = 40.0
MAX_HUMIDITY = 90.0 

WEATHER_FORECAST_DAYS = 14

WEATHER_WARNING = "Weather data is only available for the next 14 days. Your calculation maya be inaccurate since it does not include weather data for the entire night but only astronomical data. Please consider this when interpreting the results."

SCORE_WEIGHTS = {
    "airmass": 0.3,
    "altitude": 0.15,
    "moon_separation": 0.15,
    "moon_illumination": 0.15,
    "cloud_cover": 0.25
} 


# def calculate_score(heights, airmasses, moon_sep, moon_illum, cloud_cover, weights=SCORE_WEIGHTS):
#     #her bileşeni normalize et ve ağırlıkla çarp, sonra topla
#     airmass_score = 1 / airmasses
#     altitude_score = heights / 90.0
#     moon_sep_score = moon_sep / 180.0
#     moon_illum_score = 1 - moon_illum
#     cloud_cover_score = 1 - (cloud_cover /100.0)
#     return (
#         weights["airmass"] * airmass_score
#         + weights["altitude"] * altitude_score
#         + weights["moon_separation"] * moon_sep_score
#         + weights["moon_illumination"] * moon_illum_score
#         + weights["cloud_cover"] * cloud_cover_score
#     )

def safe_round(value, ndigits=1):
    if value  is None:
        return None
    try:
        if np.isnan(value):
            return None
    except TypeError:
        raise ValueError(f"Input value must be a float, int, or None, but got {type(value)}")
    return round(float(value), ndigits)


def calculate_score(heights, airmasses, moon_sep, moon_illum, moon_alt, cloud_cover, weights=SCORE_WEIGHTS, weather_available=True):
    #her bileşeni normalize et ve ağırlıkla çarp, sonra topla

    effective_moon_illum =  np.where(moon_alt < 0, 0.0, moon_illum)
    effective_moon_sep = np.where(moon_alt < 0, 1.0, moon_sep / 180.0) #ay ufkun altındaysa max puan

    components = {
        "airmass": weights["airmass"] * (1 / airmasses),
        "altitude": weights["altitude"] * (heights / 90.0),
        "moon_separation": weights["moon_separation"] * effective_moon_sep,
        "moon_illumination": weights["moon_illumination"] * (1 - effective_moon_illum),
    }

    if weather_available:
        components["cloud_cover"] = weights["cloud_cover"] * (1 - (cloud_cover / 100.0))
    else:
        components["cloud_cover"] = np.zeros_like(heights, dtype = float)

    total_score = sum(components.values())
    return total_score, components


def evaluate_target(target_dict, metrics, weather, time_sequence, weather_available=True):
    """Ham metrikleri alir, filtre + skor uygular, ozet sonuc dondurur."""
    heights = metrics["heights"]
    airmasses = metrics["airmasses"]
    moon_sep = metrics["moon_separation"]
    moon_illum = metrics["moon_illum"]
    moon_alt = metrics["moon_alt"]

    if weather_available:
        cloud_cover = weather["cloud_cover"]
        precipitation = weather["precipitation"]
        wind_speed = weather["wind_speed_10m"]
        relative_humidity = weather["relative_humidity_2m"]
        temperature = weather["temperature_2m"]

        cloud_ok = (cloud_cover <= MAX_CLOUD_COVER)
        wind_ok = (wind_speed <= MAX_WIND_SPEED)
        humidity_ok = (relative_humidity <= MAX_HUMIDITY)
        precipitation_ok = (precipitation == 0)
    else:
        nan_array = np.full_like(heights, np.nan, dtype=float)
        cloud_cover = nan_array
        precipitation = nan_array
        wind_speed = nan_array
        relative_humidity = nan_array
        temperature = nan_array

        cloud_ok = np.ones_like(heights, dtype=bool)
        wind_ok = np.ones_like(heights, dtype=bool)
        humidity_ok = np.ones_like(heights, dtype=bool) 
        precipitation_ok = np.ones_like(heights, dtype=bool)


    # can_observe = (
    #     (heights >= MIN_ALT) & (heights <= MAX_ALT)
    #     & (airmasses <= MAX_AIRMASS)
    #     & (moon_illum < MOON_ILLUM_REJECT)
    #     & (moon_sep >= MOON_SEP_MIN_DEG)
    #     & (cloud_cover <= MAX_CLOUD_COVER)
    #     & (wind_speed <= MAX_WIND_SPEED)
    #     & (relative_humidity <= MAX_HUMIDITY)
    #     & (precipitation == 0)
    # )

    effective_moon_illum = np.where(moon_alt < 0, 0.0, moon_illum) #ay ufkun atlındaysa parlaklık 0, değilse devam
    altitude_ok = (heights >= MIN_ALT) & (heights <= MAX_ALT)
    airmass_ok = (airmasses <= MAX_AIRMASS)
    # moon_illum_ok = (moon_illum < MOON_ILLUM_REJECT) old version doesnt account for moon being below horizon
    # moon_sep_ok = (moon_sep >= MOON_SEP_MIN_DEG) old version doesnt account for moon being below horizon
    moon_illum_ok = (effective_moon_illum < MOON_ILLUM_REJECT) 
    moon_sep_ok = (moon_sep >= MOON_SEP_MIN_DEG) | (moon_alt < 0) # ay ufkun altındaysa hedefe yakınlığı önemsiz yada min değerin altındaysa
    

    can_observe = (
        altitude_ok & airmass_ok & moon_illum_ok & moon_sep_ok
        & cloud_ok & wind_ok & humidity_ok & precipitation_ok
    )

    result = {
        "id": target_dict["id"],
        "name": target_dict["name"],
        "observable": bool(can_observe.any()),
        "weather_reliable": weather_available,
    }

    if not weather_available:
        result["warning"] = WEATHER_WARNING

    if can_observe.any():
        interval_minutes = (time_sequence[1] - time_sequence[0]).sec / 60.0
        result["observable_minutes"] = round(float(can_observe.sum() * interval_minutes), 1)

        total_score, components = calculate_score(heights, airmasses, moon_sep, moon_illum, moon_alt, cloud_cover, weather_available=weather_available)
        valid_scores = np.where(can_observe, total_score, -np.inf)
        best_index = np.argmax(valid_scores)
        phase = get_moon_phase(moon_illum)

        window_times = time_sequence[can_observe]
        # result["window_start_utc"] = window_times[0].iso[:16]
        # result["window_end_utc"] = window_times[-1].iso[:16]
        interval_minutes = time_sequence[1] - time_sequence[0]
        result["window_start_utc"] = window_times[0].iso[:16]
        result["window_end_utc"] = (window_times[-1] + interval_minutes).iso[:16]
        result["best_time_utc"] = time_sequence[best_index].iso[:16]
        result["best_airmass"] = round(float(airmasses[best_index]), 2)
        result["best_altitude"] = round(float(heights[best_index]), 1)
        result["moon_separation_deg"] = round(float(moon_sep[best_index]), 1)
        result["moon_illumination"] = round(float(moon_illum[best_index]), 2)
        result["moon_altitude"] = round(float(moon_alt[best_index]), 1)
        result["moon_phase"] = phase[best_index]
        result["cloud_cover"] = safe_round(cloud_cover[best_index])
        result["temperature_2m"] = safe_round(temperature[best_index])
        result["wind_speed_10m"] = safe_round(wind_speed[best_index])
        result["relative_humidity_2m"] = safe_round(relative_humidity[best_index])
        result["score"] = round(float(total_score[best_index]), 3)
        result["score_breakdown"] = {key: round(float(value[best_index]), 3) for key, value in components.items()}

        first_true = np.argmax(can_observe)                          # ilk True'nun indeksi
        last_true = len(can_observe) - 1 - np.argmax(can_observe[::-1])  # son True'nun indeksi
        window_slice = can_observe[first_true:last_true + 1]
        result["window_is_continuous"] = bool(np.all(window_slice))
    else:
        peak_index = np.argmax(heights)

        result["best_altitude"] = round(float(heights[peak_index]), 1)
        result["best_airmass"] = round(float(airmasses[peak_index]), 2)
        result["moon_separation_deg"] = round(float(moon_sep[peak_index]), 1)
        result["moon_illumination"] = round(float(moon_illum[peak_index]), 2)
        result["moon_altitude"] = round(float(moon_alt[peak_index]), 1)
        result["moon_phase"] = get_moon_phase(moon_illum)[peak_index]
        result["cloud_cover"] = safe_round(cloud_cover[peak_index])
        result["temperature_2m"] = safe_round(temperature[peak_index])
        result["wind_speed_10m"] = safe_round(wind_speed[peak_index])
        result["relative_humidity_2m"] = safe_round(relative_humidity[peak_index])

        criteria = {
            "altitude": (altitude_ok, f"Altitude must be between {MIN_ALT}° and {MAX_ALT}°"),
            "airmass": (airmass_ok, f"Airmass must be less than {MAX_AIRMASS}"),
            "moon_illumination": (moon_illum_ok, f"Moon illumination must be less than {MOON_ILLUM_REJECT}"),
            "moon_separation": (moon_sep_ok, f"Moon separation must be greater than {MOON_SEP_MIN_DEG}°"),            
        }

        if weather_available:
            criteria.update({
                "cloud_cover": (cloud_ok, f"Cloud cover must be less than {MAX_CLOUD_COVER}%"),
                "wind_speed": (wind_ok, f"Wind speed must be less than {MAX_WIND_SPEED} m/s"),
                "relative_humidity": (humidity_ok, f"Relative humidity must be less than {MAX_HUMIDITY}%"),
                "precipitation": (precipitation_ok, "No precipitation allowed"),
            })

        f_criteria = [msg for mask, msg in criteria.values() if not mask.any()]

        if not f_criteria:
            f_criteria.append("No valid observation window found, but all criteria are met. This may be due to the time sequence being too short or other factors.")
        result["rejection_reasons"] = f_criteria
        result["observable_minutes"] = 0

    return result

