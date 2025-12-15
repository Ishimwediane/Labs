# Architecture

## High-Level Design
The WeatherService depends on an abstract WeatherProvider interface.
This allows the service to remain decoupled from the data source (mock or real API).

## SOLID Principles Applied
- **Single Responsibility:** WeatherService handles business logic only.
- **Open/Closed:** New providers can be added without modifying existing code.
- **Dependency Inversion:** Service depends on abstractions, not concrete implementations.

## Folder Structure
src/weather/ # Application code
tests/ # Unit tests
docs/ # Documentation