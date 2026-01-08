import logging
import sqlite3  # Example DB; replace with PostgreSQL connection if needed

from src.config.logging_config import setup_logging
from src.pipeline.pipeline import DataPipeline
from src.pipeline.stages import DatabaseStorer, SentimentAnalyzer, TextCleaner


def main():
    # Setup logging
    setup_logging(level=logging.INFO)

    # Example database connection using SQLite (replace with PostgreSQL for integration)
    connection = sqlite3.connect(":memory:")

    # Create table for demonstration
    with connection:
        connection.execute(
            """
            CREATE TABLE sentiment_results (
                text TEXT,
                sentiment TEXT,
                score INTEGER
            )
        """
        )

    # Initialize pipeline stages
    cleaner = TextCleaner()
    analyzer = SentimentAnalyzer()
    storer = DatabaseStorer(connection=connection)

    # Create pipeline
    pipeline = DataPipeline(cleaner=cleaner, analyzer=analyzer, storer=storer)

    # Example raw texts
    raw_texts = [
        "I had a good day today!",
        "This is terrible news.",
        "Just an ordinary day.",
    ]

    for raw_text in raw_texts:
        result = pipeline.run(raw_text)
        logging.info(f"Final stored result: {result}")

    # Close connection
    connection.close()


if __name__ == "__main__":
    main()
