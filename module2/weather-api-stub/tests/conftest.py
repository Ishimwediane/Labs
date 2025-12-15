# tests/conftest.py

import pytest
from src.weather.service import WeatherService
from src.weather.provider import MockWeatherProvider


@pytest.fixture
def mock_provider():
    """Fixture for initializing a MockWeatherProvider."""
    return MockWeatherProvider()


@pytest.fixture
def weather_service(mock_provider):
    """Fixture for initializing WeatherService with MockWeatherProvider."""
    service = WeatherService(mock_provider)
    return service
