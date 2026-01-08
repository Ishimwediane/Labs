import psycopg2
import pytest
from src.pipeline.pipeline import DataPipeline
from src.pipeline.stages import DatabaseStorer, SentimentAnalyzer, TextCleaner
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


def test_full_pipeline(postgres_container):
    # Connect to the test PostgreSQL container
    connection = psycopg2.connect(
        dbname=postgres_container.POSTGRES_DB,
        user=postgres_container.POSTGRES_USER,
        password=postgres_container.POSTGRES_PASSWORD,
        host=postgres_container.get_container_host_ip(),
        port=postgres_container.get_exposed_port(postgres_container.port_to_expose),
    )

    # Create table
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE sentiment_results (
                text TEXT,
                sentiment TEXT,
                score INTEGER
            )
        """
        )
        connection.commit()

    # Initialize pipeline stages
    cleaner = TextCleaner()
    analyzer = SentimentAnalyzer()
    storer = DatabaseStorer(connection=connection)
    pipeline = DataPipeline(cleaner=cleaner, analyzer=analyzer, storer=storer)

    raw_text = "I had an excellent day!"
    result = pipeline.run(raw_text)

    # Verify the result returned by the pipeline
    assert result["text"] == cleaner.process(raw_text)
    assert result["sentiment"] == "positive"

    # Verify the data is actually in the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT text, sentiment, score FROM sentiment_results")
        db_result = cursor.fetchone()

    assert db_result[0] == result["text"]
    assert db_result[1] == result["sentiment"]
    assert db_result[2] == result["score"]

    # Close connection
    connection.close()
