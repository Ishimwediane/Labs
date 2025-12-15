# tests/test_service.py

import pytest
from src.weather.service import WeatherService
from src.weather.provider import MockWeatherProvider
from src.weather.exceptions import CityNotFoundError, InvalidAPIKeyError


def test_get_forecast_valid_city(weather_service):
    city = "Kigali"
    forecast = weather_service.get_forecast(city)

    # Ensure forecast is a dictionary with expected keys
    assert isinstance(forecast, dict)
    assert "temperature" in forecast
    assert "description" in forecast


# unknown cities
def test_get_forecast_unknown_city(weather_service):
    with pytest.raises(CityNotFoundError):
        weather_service.get_forecast("UnknownCity")


# Invalid API key
def test_get_forecast_invalid_api_key():
    # Provide a wrong API key to the mock provider
    provider = MockWeatherProvider(api_key="wrong_key")
    service = WeatherService(provider)

    with pytest.raises(InvalidAPIKeyError):
        service.get_forecast("Kigali")


# Mocking provider method
def test_get_forecast_calls_provider(mocker, weather_service):
    # Patch the provider's get_forecast method
    mock = mocker.patch(
        "src.weather.provider.MockWeatherProvider.get_forecast",
        return_value={"temperature": 25, "description": "Sunny"},
    )

    result = weather_service.get_forecast("Kigali")

    # Ensure the provider method was called once with the correct city
    mock.assert_called_once_with("Kigali")

    # Validate returned data
    assert result["temperature"] == 25
    assert result["description"] == "Sunny"


# All predefined cities return forecast
def test_all_predefined_cities(weather_service):
    # Suppose MockWeatherProvider has a predefined list of cities
    cities = ["Kigali", "Nairobi", "Addis Ababa", "Dar es Salaam"]
    for city in cities:
        forecast = weather_service.get_forecast(city)
        assert isinstance(forecast, dict)
        assert "temperature" in forecast
        assert "description" in forecast
