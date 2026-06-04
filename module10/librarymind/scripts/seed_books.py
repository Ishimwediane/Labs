import json
import logging
import os
import sys

# Add the project root to sys.path to allow imports from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding_service import EmbeddingService
from app.infrastructure.vector_store import ChromaVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def seed_books():
    """
    Load books from JSON, generate embeddings, and store them in the vector database.
    """
    data_path = "data/books.json"
    if not os.path.exists(data_path):
        logger.error(f"Data file not found at {data_path}")
        return

    # 1. Load data
    with open(data_path, "r") as f:
        books = json.load(f)
    
    logger.info(f"Loaded {len(books)} books from {data_path}")

    # 2. Prepare text for embedding
    # We combine multiple fields to give the embedding model more context
    texts_to_embed = [
        f"Title: {b['title']}. Author: {b['author']}. Genre: {b['genre']}. "
        f"Year: {b['year']}. Description: {b['description']}"
        for b in books
    ]

    # 3. Generate embeddings
    embed_service = EmbeddingService()
    logger.info("Generating embeddings for books...")
    embeddings = embed_service.embed_texts(texts_to_embed)

    # 4. Store in Vector DB
    vector_store = ChromaVectorStore()
    logger.info("Upserting books into ChromaVectorStore...")
    vector_store.upsert_books(books, embeddings)

    print(f"\n--- Seeding Complete ---")
    print(f"Total books loaded: {len(books)}")
    print(f"Total records in Chroma: {vector_store.count()}")

if __name__ == "__main__":
    seed_books()
