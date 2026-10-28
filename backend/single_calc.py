from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u
from astroplan import Observer
import numpy as np

tug = EarthLocation(
    lat = 36.22825 * u.deg,
    lon = 30.335 * u.deg,
    height = 2500 *u.m,
)

hedef = SkyCoord(
    ra = 56.600833333333334 * u.deg,
    dec = 24.11388888888889 * u.deg,
    unit = (u.deg, u.deg),
    frame = "icrs",
)

print(hedef.ra, hedef.dec)
print(hedef.ra.to_string(unit= "hourangle", sep= "hms"))

observer = Observer(location = tug, name ="TUG")
obs_date = Time("2027-01-30 18:00:00")
sunset = observer.sun_set_time(obs_date, which="next") #after obsservation date, next sunset time
sunrise = observer.sun_rise_time(sunset, which="next") #after observayion date, next sunrise time

period = np.linspace(sunset.jd, sunrise.jd, 60) #60 periods in between sunset and sunrise
sequence = Time(period, format="jd") #jd is julian date 

#altaz = altitude + azimuth = yükseklik + yön
altaz_frame = AltAz(obstime=sequence, location=tug)
target_altaz = hedef.transform_to(altaz_frame)
heights = target_altaz.alt.deg #alt=altitude in angle, az = azimuth in angle
airmasses = target_altaz.secz #secz = secant of the zenith angle (between zenith and target)


min_alt, max_alt = 20, 80
can_observe = (heights >= min_alt) & (heights <= max_alt)

gozlem_yapilabilir = can_observe.sum()
print(gozlem_yapilabilir)
print(f"Observatory: {observer.name}: ({tug.lat:.3f}, {tug.lon:.3f})")
print(f"Gece: {sunset.iso} -> {sunrise.iso} (UTC)")
print(f"Teleskop limiti: {min_alt}° - {max_alt}°\n")

print("Zaman (UTC)          Yukseklik (deg)   Airmass   Gozlem?")
print("-" * 60)
for t, y, a, g in zip(sequence, heights, airmasses, can_observe):
    isaret = "yes" if g else "no"
    print(f"{t.iso[:16]}      {y:6.1f}            {a:6.2f}     {isaret}")

if can_observe.any():
    valid_airmasses = np.where(can_observe, airmasses, np.inf)
    bestindex = np.argmin(valid_airmasses)

    frame_time = sequence[can_observe]
    frame_start = frame_time[0]
    frame_finish = frame_time[-1]

    print("\n--- SUMMARY ---")
    print(f"Gozlemlenebilir pencere: {frame_start.iso[:16]} -> {frame_finish.iso[:16]} UTC")
    print(f"Best time (lowest): {sequence[bestindex].iso[:16]}")
    print(f"Airmass at that point: {airmasses[bestindex]:.2f}")
    print(f"Height at that point: {heights[bestindex]:.1f} degrees")
else:
    print("No observations possible within the specified altitude limits.")


print(f"Sunset: {sunset.iso}, Sunrise: {sunrise.iso}")