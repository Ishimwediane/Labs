import logging

from app.providers.resilient_service import ResilientAIService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

def run_test():
    service = ResilientAIService()

    prompt = "Say hello in one short sentence."
    system = "You are concise and polite."

    result = service.generate(
        prompt=prompt,
        system=system,
        temperature=0.2,
        max_tokens=500,
    )

    print("\nRESULT:")
    print(result)

if __name__ == "__main__":
    run_test()
