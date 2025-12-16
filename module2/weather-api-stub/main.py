from colorama import Fore, init
from src.service import WeatherService
from src.provider.mock import MockWeatherProvider
from src.exceptions import CityNotFoundError, InvalidAPIKeyError

# Initialize colorama
init(autoreset=True)


def main():
    print(Fore.CYAN + "=== Weather API Stub CLI ===")
    api_key = input("Enter API key (default='valid_key'): ").strip() or "valid_key"
    provider = MockWeatherProvider(api_key=api_key)
    service = WeatherService(provider)

    while True:
        city = input("\nEnter city name (or 'exit' to quit): ").strip()
        if city.lower() == "exit":
            print(Fore.CYAN + "Exiting Weather CLI. Goodbye!")
            break

        try:
            print(Fore.BLUE + f"INFO: Forecast request received for city={city}")
            forecast = service.get_forecast(city)
            print(
                Fore.GREEN
                + f"Forecast for {city}: {forecast.temperature}°C,"
                + f" {forecast.description}"
            )
        except CityNotFoundError:
            print(Fore.RED + f"Error: City '{city}' not found in predefined data.")
        except InvalidAPIKeyError:
            print(Fore.RED + "Error: Invalid API key.")
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
