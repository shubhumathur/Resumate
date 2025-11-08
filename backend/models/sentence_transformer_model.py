"""
Sentence transformer model for generating embeddings.
Supports chunked embeddings for long texts to avoid truncation.
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import os
import numpy as np
from functools import lru_cache


@lru_cache(maxsize=1)
def get_sentence_transformer_model(model_name: str = None) -> SentenceTransformer:
    """
    Get or initialize sentence transformer model (singleton pattern).
    Uses a stronger model (all-mpnet-base-v2) by default for better accuracy.
    
    Args:
        model_name: Name of the model to use
        
    Returns:
        SentenceTransformer model instance
    """
    if model_name is None:
        # Use a stronger model for better semantic similarity
        # Fallback to lighter model if specified in env or if download fails
        model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-mpnet-base-v2")
    
    try:
        model = SentenceTransformer(model_name)
        return model
    except Exception as e:
        # Fallback to lighter model if the preferred one fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load {model_name}, falling back to all-MiniLM-L6-v2: {e}")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model


def generate_embeddings(
    texts: Union[str, List[str]],
    model_name: str = None,
    chunk_size: int = 300
) -> Union[List[float], List[List[float]]]:
    """
    Generate embeddings for text(s) with chunking support for long texts.
    Avoids truncation by chunking texts that exceed token limits.
    
    Args:
        texts: Single text or list of texts
        model_name: Optional model name
        chunk_size: Number of tokens per chunk (default: 300)
        
    Returns:
        Single embedding or list of embeddings
    """
    model = get_sentence_transformer_model(model_name)
    
    is_single = isinstance(texts, str)
    if is_single:
        texts = [texts]
    
    # Process each text with chunking if needed
    embeddings = []
    for text in texts:
        if not text:
            # Empty text - return zero vector
            emb = model.encode("", convert_to_numpy=True)
            embeddings.append(emb)
            continue
        
        # Estimate token count (rough approximation: ~1 token per word)
        words = text.split()
        token_count = len(words)
        
        # If text is short enough, encode directly
        if token_count <= chunk_size:
            emb = model.encode(text, convert_to_numpy=True)
            embeddings.append(emb)
        else:
            # Chunk the text and average embeddings
            emb = embed_long_text(model, text, chunk_size)
            embeddings.append(emb)
    
    embeddings = np.array(embeddings)
    
    if is_single:
        return embeddings[0].tolist()
    
    return embeddings.tolist()


def embed_long_text(model: SentenceTransformer, text: str, chunk_size: int = 300) -> np.ndarray:
    """
    Embed long text by chunking and averaging embeddings (mean pooling).
    Prevents truncation issues with sentence-transformers.
    
    Args:
        model: SentenceTransformer model
        text: Long text to embed
        chunk_size: Number of tokens per chunk
        
    Returns:
        Averaged embedding vector
    """
    # Split text into words
    words = text.split()
    
    # Create chunks
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    if not chunks:
        # Fallback for empty text
        return model.encode("", convert_to_numpy=True)
    
    # Encode each chunk
    chunk_embeddings = model.encode(chunks, convert_to_numpy=True)
    
    # Average embeddings (mean pooling)
    averaged_embedding = np.mean(chunk_embeddings, axis=0)
    
    return averaged_embedding

