from astropy.time import Time, TimeDelta
import numpy as np
import pytest
import astropy.units as u
from scoring import safe_round, calculate_score, evaluate_target, SCORE_WEIGHTS

@pytest.fixture
def sample_time_sequence():
    # 5 zaman aralığı, 30 dakika aralıklarla
    return Time("2025-06-15T20:00:00") + np.arange(5) * 30 * u.minute

@pytest.fixture
def sample_target_dict():
    return {
        "id": "M31",
        "name": "Andromeda Galaxy",
        "ra": 10.68470833,  # RA in degrees
        "dec": 41.26875,    # Dec in degrees
        "type": "Galaxy",
    }

@pytest.fixture
def sample_metrics_ok():
    return{
        "heights": np.array([30.0, 45.0, 60.0, 75.0, 90.0]),
        "airmasses": np.array([2.0, 1.5, 1.2, 1.1, 1.0]),
        "moon_separation": np.array([5.0, 15.0, 30.0, 60.0, 90.0]),
        "moon_illum": np.array([0.9, 0.7, 0.5, 0.3, 0.1]),
        "moon_alt": np.array([-10.0, -5.0, 0.0, 5.0, 10.0]),  # Moon below horizon for first two
    }

@pytest.fixture
def sample_weather_ok():
    return {
        "cloud_cover": np.array([80.0, 60.0, 40.0, 20.0, 10.0]),  # Cloud cover percentages
        "precipitation": np.array([0.0, 0.0, 0.1, 0.2, 0.0]),  # Precipitation in mm
        "wind_speed_10m": np.array([10.0, 20.0, 40.0, 55.0, 70.0]),  # Wind speed in m/s
        "relative_humidity_2m": np.array([90.0, 80.0, 70.0, 60.0, 50.0]),  # Relative humidity percentages
        "temperature_2m": np.array([5.0, 10.0, 15.0, 20.0, 25.0]),  # Temperature in Celsius
    }

@pytest.fixture
def sample_metrics_none():
    return {
        "heights": np.array([30.0, 45.0, 60.0, 75.0, 90.0]),
        "airmasses": np.array([2.0, 1.5, 1.2, 1.1, 1.0]),
        "moon_separation": np.array([5.0, 15.0, 30.0, 60.0, 90.0]),
        "moon_illum": np.array([0.9, 0.7, 0.5, 0.3, 0.1]),
        "moon_alt": np.array([-10.0, -5.0, 0.0, 5.0, 10.0]),
    }

@pytest.fixture
def sample_weather_none():
    return {
        "cloud_cover": np.array([90.0, 90.0, 90.0, 90.0, 90.0]),
        "precipitation": np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
        "wind_speed_10m": np.array([10.0, 10.0, 10.0, 10.0, 10.0]),
        "relative_humidity_2m": np.array([50.0, 50.0, 50.0, 50.0, 50.0]),
        "temperature_2m": np.array([15.0, 15.0, 15.0, 15.0, 15.0]),
    }

@pytest.fixture
def sample_metrics_all():
    return {
        "heights": np.array([30.0, 45.0, 60.0, 75.0, 79.0]),
        "airmasses": np.array([2.0, 1.5, 1.2, 1.1, 1.0]),
        "moon_separation": np.array([5.0, 15.0, 30.0, 60.0, 90.0]),
        "moon_illum": np.array([0.9, 0.7, 0.5, 0.3, 0.1]),
        "moon_alt": np.array([-10.0, -5.0, 0.0, 5.0, 10.0]),
    }

@pytest.fixture
def sample_weather_all():
    return {
        "cloud_cover": np.array([0.0, 2.0, 10.0, 5.0, 10.0]),
        "precipitation": np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
        "wind_speed_10m": np.array([5.0, 10.0, 15.0, 20.0, 25.0]),
        "relative_humidity_2m": np.array([20.0, 25.0, 30.0, 40.0, 50.0]),
        "temperature_2m": np.array([15.0, 15.0, 15.0, 15.0, 10.0]),
    }