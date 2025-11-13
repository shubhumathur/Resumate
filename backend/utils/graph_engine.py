from __future__ import annotations

from typing import Any, Dict, Iterable

from backend.db.neo4j_client import get_driver


def store_resume_graph(resume_data: Dict[str, Any]) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.execute_write(_create_resume_nodes, resume_data)


def _create_resume_nodes(tx, data: Dict[str, Any]) -> None:
    resume_id = data.get("id")
    if not resume_id:
        raise ValueError("resume_data must include an 'id' field.")

    name = data.get("name", "Unknown")
    skills: Iterable[str] = data.get("skills", []) or []
    experiences: Iterable[str] = data.get("experiences", []) or []

    tx.run(
        "MERGE (r:Resume {id: $id}) "
        "ON CREATE SET r.name = $name "
        "ON MATCH SET r.name = $name",
        id=resume_id,
        name=name,
    )

    for skill in skills:
        tx.run(
            """
            MERGE (s:Skill {name: $skill})
            MERGE (r:Resume {id: $id})-[:HAS_SKILL]->(s)
            """,
            skill=skill,
            id=resume_id,
        )

    for exp in experiences:
        tx.run(
            """
            MERGE (r:Resume {id: $id})
            CREATE (e:Experience {description: $exp})
            MERGE (r)-[:HAS_EXPERIENCE]->(e)
            """,
            exp=exp,
            id=resume_id,
        )


def store_job_graph(job_data: Dict[str, Any]) -> None:
    driver = get_driver()
    with driver.session() as session:
        session.execute_write(_create_job_nodes, job_data)


def _create_job_nodes(tx, data: Dict[str, Any]) -> None:
    job_id = data.get("id")
    if not job_id:
        raise ValueError("job_data must include an 'id' field.")

    title = data.get("title", "Unknown Role")
    skills: Iterable[str] = data.get("skills", []) or []

    tx.run(
        "MERGE (j:Job {id: $id}) "
        "ON CREATE SET j.title = $title "
        "ON MATCH SET j.title = $title",
        id=job_id,
        title=title,
    )

    for skill in skills:
        tx.run(
            """
            MERGE (s:Skill {name: $skill})
            MERGE (j:Job {id: $id})-[:REQUIRES_SKILL]->(s)
            """,
            skill=skill,
            id=job_id,
        )


def fetch_shared_skills(limit: int = 10) -> Iterable[str]:
    driver = get_driver()
    with driver.session() as session:
        records = session.run(
            """
            MATCH (r:Resume)-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:Job)
            RETURN DISTINCT s.name AS skill
            LIMIT $limit
            """,
            limit=limit,
        )
        return [record["skill"] for record in records]

