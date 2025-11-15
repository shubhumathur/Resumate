from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j+s://97a53bd0.databases.neo4j.io",
    auth=("neo4j", "neo4j123")
)

with driver.session() as session:
    result = session.run("RETURN 'Neo4j connection successful' AS msg")
    print(result.single()["msg"])
