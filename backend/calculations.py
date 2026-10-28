from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_body, get_sun
from astropy.time import Time
from astropy import units as u
from astroplan import Observer, moon_illumination
import numpy as np

TIME_RESOLUTION = 60  # dakika cinsinden
def get_time_sequence(obs_date, location, num = TIME_RESOLUTION):
    observer = Observer(location=location, name="TUG")
    obs_date = Time(obs_date, scale="utc")
    sunset = observer.sun_set_time(obs_date, which="next")
    sunrise = observer.sun_rise_time(sunset, which="next")
    period = np.linspace(sunset.jd, sunrise.jd, num)
    sequence = Time(period, format="jd")
    return sequence

def compute_target_metrics(target_dict, location, time_sequence):
    coord = SkyCoord(
        ra=float(target_dict["ra"]) * u.deg,
        dec=float(target_dict["dec"]) * u.deg,
        unit=(u.deg, u.deg),
        frame="icrs",
    )

    altaz_frame = AltAz(obstime=time_sequence, location=location)
    target_altaz = coord.transform_to(altaz_frame)
    moon_pos = get_body("moon", time_sequence, location)
    moon_altaz =moon_pos.transform_to(altaz_frame)

    return {
        "heights": target_altaz.alt.deg,
        "airmasses": target_altaz.secz,
        "moon_separation": coord.separation(moon_pos).deg,
        "moon_illum": moon_illumination(time_sequence),
        "moon_alt": moon_altaz.alt.deg,
    }

def get_moon_phase(moon_illum):
    trend = np.gradient(moon_illum) # Waxing (buyuyor) mi waning (kuculuyor) mu -- ardisik iki nokta arasindaki farka bakariz
    names = []
    for pct, growing in zip(moon_illum, trend>= 0):
        if  pct < 0.01:
            names.append("New Moon")
        elif pct < 0.25:
            names.append("Waxing Crescent" if growing else "Waning Crescent")
        elif pct < 0.5:
            names.append("First Quarter" if growing else "Last Quarter")
        elif pct < 0.75:
            names.append("Waxing Gibbous" if growing else "Waning Gibbous")
        else:
            names.append("Full Moon")

    return names