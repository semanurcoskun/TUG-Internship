import numpy as np
from scoring import safe_round, calculate_score, evaluate_target, SCORE_WEIGHTS
import pytest

# def test_safe_round_normal_value():
#     value= 3.14159
#     result = safe_round(value, ndigits=2)
#     # Test that safe_round correctly rounds a normal float value to the specified number of digits
#     assert result == 3.14

# def test_safe_round_none_value():
#     # Test that safe_round returns None when the input value is None
#     assert safe_round(None) is None

# def test_safe_round_nan_value():
#     # Test that safe_round returns None when the input value is NaN
#     assert safe_round(np.nan) is None

# def test_safe_round_default_ndigits():
#     # Test that safe_round uses the default number of digits (1) when not specified
#     assert safe_round(3.14159) == 3.1

@pytest.mark.parametrize("value, ndigits, expected", [
    (3.14159, 2, 3.14),
    (2.71828, 3, 2.718),
    (1.41421, 0, 1.0),
    (None, 1, None),
    (np.nan, 1, None)
])
def test_safe_round(value, ndigits, expected):
    assert(safe_round(value, ndigits) == expected)
# def test_safe_round(value, ndigits, expected):
#     with pytest.raises(AssertionError):
#         assert not safe_round(value, ndigits) == expected


def test_calculate_score_basic_weather_available():
    # Arrange: single time point, moon above horizon
    heights = np.array([60.0])
    airmasses = np.array([1.2])
    moon_separations = np.array([90.0])
    moon_illuminations = np.array([0.3])
    moon_alt = np.array([10.0])  # Moon is above the horizon
    cloud_cover = np.array([20.0])

    total_score, components = calculate_score(heights, airmasses, moon_separations, moon_illuminations, moon_alt, cloud_cover, weather_available=True)

    expected_airmass = SCORE_WEIGHTS['airmass'] * (1 / 1.2)
    expected_altitude = SCORE_WEIGHTS["altitude"] * (60.0 / 90.0)
    expected_moon_sep = SCORE_WEIGHTS["moon_separation"] * (90.0 / 180.0)
    expected_moon_illum = SCORE_WEIGHTS["moon_illumination"] * (1 - 0.3)
    expected_cloud = SCORE_WEIGHTS["cloud_cover"] * (1 - (20.0 / 100.0))
    expected_total = (
        expected_airmass + expected_altitude + expected_moon_sep
        + expected_moon_illum + expected_cloud
    )

    assert total_score[0] == pytest.approx(expected_total)


def test_calculate_score_moon_below_horizon():
    # Arrange: single time point, moon below horizon
    #  so that moon illumination and separation should not contribute to the score
    heights = np.array([60.0])
    airmasses = np.array([1.2])
    moon_separations = np.array([1.0]) #bad value on purpose
    moon_illuminations = np.array([0.99]) #bad value on purpose
    moon_alt = np.array([-10.0])  # Moon is below the horizon
    cloud_cover = np.array([20.0])

    total_score, components = calculate_score(heights, airmasses, moon_separations, moon_illuminations, moon_alt, cloud_cover, weather_available=True)

    expected_cloud = SCORE_WEIGHTS["cloud_cover"] * (1 - (20.0 / 100.0)) 
    expected_airmass = SCORE_WEIGHTS['airmass'] * (1 / 1.2)
    expected_altitude = SCORE_WEIGHTS["altitude"] * (60.0 / 90.0)        
    expected_moon_sep = SCORE_WEIGHTS["moon_separation"] * 1.0  #effective 1 verdim
    expected_moon_illum = SCORE_WEIGHTS["moon_illumination"] * (1 - 0.0) #effective değere 0 veriyom
    expected_total = (
            expected_airmass + expected_altitude + expected_moon_sep
            + expected_moon_illum + expected_cloud
        )
    
    assert total_score[0] == pytest.approx(expected_total)

    assert components["moon_separation"][0] == pytest.approx(expected_moon_sep)
    assert components["moon_illumination"][0] == pytest.approx(expected_moon_illum)

def test_calculate_score_no_weather_data():
    #arrange: single time point, moon above horizon
    #but no weather data available, cloud cover 0

    heights = np.array([60.0])
    airmasses = np.array([1.2])
    moon_separation = np.array([90.0])
    moon_illuminations = np.array([0.3])
    moon_alt = np.array([10.0])
    cloud_cover = np.array([20.0]) #should be ignored

    total_score, components = calculate_score(heights, airmasses, moon_separation, moon_illuminations, moon_alt, cloud_cover, weather_available=False)

    expected_airmass = SCORE_WEIGHTS['airmass'] * (1 / 1.2)
    expected_altitude = SCORE_WEIGHTS["altitude"] * (60.0 / 90.0)
    expected_moon_sep = SCORE_WEIGHTS["moon_separation"] * (90.0 / 180.0)
    expected_moon_illum = SCORE_WEIGHTS["moon_illumination"] * (1 - 0.3)
    expected_cloud = 0.0  # Cloud cover should not contribute to the score
    expected_total = (
        expected_airmass + expected_altitude + expected_moon_sep
        + expected_moon_illum + expected_cloud
    )

    assert total_score[0] == pytest.approx(expected_total)
    assert components["cloud_cover"][0] == pytest.approx(expected_cloud)

def test_evaluate_target_mixed(sample_target_dict, sample_metrics_ok, sample_weather_ok, sample_time_sequence):
    results = evaluate_target(sample_target_dict, sample_metrics_ok, sample_weather_ok, sample_time_sequence, weather_available=True)
    assert results["observable"] is True
    assert results["observable_minutes"] > 0
    assert results["id"] == "M31"
    assert results["name"] == "Andromeda Galaxy"
    assert results["best_altitude"] == pytest.approx(45.0)
    assert results["best_airmass"] == pytest.approx(1.5)
    assert results["moon_separation_deg"] == pytest.approx(15.0)
    assert results["cloud_cover"] == pytest.approx(60.0)

def test_evaluate_target_none(
        sample_target_dict, sample_metrics_none, sample_weather_none, sample_time_sequence):
    results = evaluate_target(sample_target_dict, sample_metrics_none, sample_weather_none, sample_time_sequence, weather_available=True)

    assert results["observable"] is False
    assert results["observable_minutes"] == 0
    assert "cloud cover" in " ".join(results["rejection_reasons"]).lower()

def test_evaluate_target_all(
        sample_target_dict, sample_metrics_all, sample_weather_all, sample_time_sequence):
    results = evaluate_target(sample_target_dict, sample_metrics_all, sample_weather_all, sample_time_sequence, weather_available=True)

    assert results["observable"] is True
    assert results["observable_minutes"] == pytest.approx(5 * 30)  # 5 time points * 30 minutes each
    assert results["window_is_continuous"] is True