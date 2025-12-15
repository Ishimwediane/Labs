# Testing Strategy

## Test Levels
- Unit tests for WeatherService and providers.
- Integration tests for service + provider.

## Tools
- pytest for running tests
- pytest-mock for mocking dependencies
- coverage.py for measuring test coverage

## Fixtures
- Reusable pytest fixtures to initialize WeatherService.

## Mocking Strategy
- MockWeatherProvider returns predefined data for tests.
- Dependencies are isolated for unit tests.
