import openmeteo_requests
import pandas as pd
om_client = openmeteo_requests.AsyncClient()
import numpy as np
from astropy.coordinates import EarthLocation

async def get_hourly_weather(location: EarthLocation, start_date: str, end_date: str):
    base_url = "https://api.open-meteo.com/v1/forecast"

    # TUG'un konumunu Astropy'den çekip enlem/boylam değerlerini alıyoruz
    latitude = location.lat.deg
    longitude = location.lon.deg

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly" : ["temperature_2m", "precipitation", "wind_speed_10m", "cloud_cover", "relative_humidity_2m"],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC",
        }

    try:
        responses = await om_client.weather_api(base_url, params=params)
        response = responses[0] #process first response only

        """print(f"Coordinates: {latitude}, {longitude}")
        print(f"Elevation: {response.Elevation()} m asl") #deniz seviyesine göre
        print(f"Timezone difference to GMT+0 : {response.UtcOffsetSeconds()} seconds")"""

        hourly = response.Hourly()
        hourly_data = {
            "date": pd.date_range(
                start = pd.to_datetime(hourly.Time(), unit='s', utc=True),
                end = pd.to_datetime(hourly.TimeEnd(), unit='s', utc=True),
                freq = pd.Timedelta(seconds=hourly.Interval()),
                inclusive = "left",
            ),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(), #hourlynin ilk verisi olan yerden 2m yüksekteki sıcaklığı verir
            "precipitation": hourly.Variables(1).ValuesAsNumpy(), #hourlynin ikinci verisi olan yağış miktarını verir
            "wind_speed_10m": hourly.Variables(2).ValuesAsNumpy(), #hourlynin üçüncü verisi olan yerden 10m yüksekteki rüzgar hızını verir
            "cloud_cover": hourly.Variables(3).ValuesAsNumpy(), #hourlynin dördüncü verisi olan bulut örtüsünü verir
            "relative_humidity_2m": hourly.Variables(4).ValuesAsNumpy(), #hourlynin beşinci verisi olan yerden 2m yüksekteki bağıl nemi verir
        }

        return pd.DataFrame(hourly_data)

    except Exception as e:
        return {"error": str(e)}


def match_weather_to_time_sequence(weather_df, time_sequence):
    epoch = pd.Timestamp("1970-01-01", tz="utc")   
    weather_unix = (weather_df["date"] - epoch) / pd.Timedelta(seconds=1)
    sequence_unix = time_sequence.unix

    matched = {}
    for col in ["temperature_2m", "precipitation", "wind_speed_10m", "cloud_cover", "relative_humidity_2m"]:
        matched[col] = np.interp(sequence_unix, weather_unix, weather_df[col].values)
    return matched
