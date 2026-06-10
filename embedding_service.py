"""
AEME - Embedding Service
=========================
Real semantic embeddings using sentence-transformers.
"""

import asyncio
import numpy as np
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class EmbeddingService:
    """Singleton service for generating semantic embeddings"""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if self._initialized:
            return
        self.model_name = model_name
        self.model = None
        self.dimension = 384
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = True

    async def initialize(self):
        """Load the sentence-transformers model"""
        if self.model is not None:
            return
        
        if HAS_TRANSFORMERS:
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor, 
                lambda: SentenceTransformer(self.model_name)
            )
            print(f"✓ Loaded embedding model: {self.model_name}")
        else:
            print("⚠️  WARNING: sentence-transformers not installed. Using mock embeddings.")

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not HAS_TRANSFORMERS or self.model is None:
            # Fallback to mock embedding
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(self.dimension).tolist()
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            lambda: self.model.encode(text, convert_to_numpy=True).tolist()
        )
        return embedding


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """Get singleton embedding service instance"""
    service = EmbeddingService(model_name)
    return service


def get_embedding_dimension(model_name: str = "all-MiniLM-L6-v2") -> int:
    """Get embedding dimensionality"""
    return 384
