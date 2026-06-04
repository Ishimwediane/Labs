import logging
from typing import List, Dict, Any, Optional

import chromadb
from app.config import get_settings

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    """
    A vector store implementation using ChromaDB with persistent storage.
    Handles embedding storage and semantic search.
    """

    def __init__(self):
        self.settings = get_settings()
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaVectorStore initialized at: {self.settings.CHROMA_PERSIST_DIR}")

    def _get_or_create_collection(self):
        """Get the existing collection or create a new one with cosine similarity."""
        return self.client.get_or_create_collection(
            name=self.settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    def upsert_books(self, books: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """
        Store or update books and their embeddings in the vector store.
        """
        if not books or not embeddings:
            logger.warning("No books or embeddings provided for upsert.")
            return

        ids = [b["id"] for b in books]
        metadatas = [
            {
                "title": b["title"],
                "author": b["author"],
                "genre": b["genre"],
                "year": b["year"],
                "description": b["description"]
            }
            for b in books
        ]
        # We use the description as the primary document text for convenience
        documents = [b["description"] for b in books]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info(f"Successfully upserted {len(books)} books into Chroma.")

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for the most similar books based on a query embedding.
        Returns a list of structured book data with similarity scores.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances", "documents"]
        )

        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # NOTE on Distance vs Similarity:
                # Chroma with 'cosine' space returns Cosine Distance (1 - similarity).
                # 0.0 means identical, 1.0 means orthogonal, 2.0 means opposite.
                # To get a 'similarity score' where 1.0 is best, we use (1 - distance).
                distance = results["distances"][0][i]
                similarity_score = 1.0 - distance
                
                metadata = results["metadatas"][0][i]
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "title": metadata["title"],
                    "author": metadata["author"],
                    "genre": metadata["genre"],
                    "year": metadata["year"],
                    "description": metadata["description"],
                    "score": round(similarity_score, 4)
                })

        return formatted_results

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()
