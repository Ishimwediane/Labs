# Requirements

## Functional Requirements
- The service shall return weather data for predefined cities.
- The service shall raise `CityNotFoundError` for unknown cities.
- The service shall raise `InvalidAPIKeyError` for invalid API keys.
- The service shall provide a `get_forecast(city: str)` method.

## Non-Functional Requirements
- Near 100% test coverage.
- Strict TDD workflow (Red → Green → Refactor).
- Clean code with SOLID principles.
- Python 3.11+ compatible.
- Pre-commit hooks for code quality.
