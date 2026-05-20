import logging
import os
import sys

# Add the project root to sys.path to allow imports from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding_service import EmbeddingService
from app.infrastructure.vector_store import ChromaVectorStore

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

def test_search():
    """
    Test semantic search with specific queries.
    """
    embed_service = EmbeddingService()
    vector_store = ChromaVectorStore()

    print(f"Current collection count: {vector_store.count()}")

    queries = [
        "space travel adventure",
        "historical romance in England"
    ]

    for query in queries:
        print(f"\n>>> Searching for: '{query}'")
        
        # 1. Embed the query
        query_embedding = embed_service.embed_text(query)
        
        # 2. Search
        results = vector_store.search(query_embedding, top_k=3)
        
        # 3. Print results
        if not results:
            print("No results found.")
            continue

        for i, res in enumerate(results):
            print(f"  {i+1}. [{res['score']}] {res['title']} by {res['author']}")
            print(f"     Genre: {res['genre']}")
            # print(f"     Description: {res['description'][:100]}...") # Optional: show snippet

if __name__ == "__main__":
    test_search()
