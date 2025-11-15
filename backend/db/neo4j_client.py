import os
from functools import lru_cache

from neo4j import GraphDatabase, basic_auth


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


@lru_cache(maxsize=1)
def _get_driver():
    if not (NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD):
        raise RuntimeError("Neo4j configuration missing. Ensure NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are set.")

    return GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))


def get_driver():
    """
    Retrieve a singleton Neo4j driver instance. Caller is responsible for closing the
    driver on application shutdown (handled in FastAPI lifespan events if configured).
    """
    return _get_driver()


def close_driver():
    """Close the cached Neo4j driver (mainly for tests)."""
    driver = _get_driver()
    driver.close()
    _get_driver.cache_clear()


