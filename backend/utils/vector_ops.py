"""
Vector operations for semantic similarity and embeddings.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Union


def compute_cosine_similarity(
    vector1: Union[List[float], np.ndarray],
    vector2: Union[List[float], np.ndarray]
) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vector1: First vector
        vector2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    vec1 = np.array(vector1).reshape(1, -1)
    vec2 = np.array(vector2).reshape(1, -1)
    similarity = cosine_similarity(vec1, vec2)[0][0]
    return float(similarity)


def normalize_vector(vector: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Normalize a vector to unit length.
    
    Args:
        vector: Input vector
        
    Returns:
        Normalized vector
    """
    vec = np.array(vector)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def compute_batch_similarity(
    query_vector: Union[List[float], np.ndarray],
    candidate_vectors: List[Union[List[float], np.ndarray]]
) -> List[float]:
    """
    Compute cosine similarity between a query vector and multiple candidate vectors.
    
    Args:
        query_vector: Query vector
        candidate_vectors: List of candidate vectors
        
    Returns:
        List of similarity scores
    """
    query = np.array(query_vector).reshape(1, -1)
    candidates = np.array(candidate_vectors)
    similarities = cosine_similarity(query, candidates)[0]
    return similarities.tolist()

