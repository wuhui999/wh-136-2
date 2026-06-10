from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import Trench, Stratum, Artifact, User
from schemas import RelationGraph, RelationNode, RelationEdge

router = APIRouter(prefix="/api/relations", tags=["关联图"])


@router.get("/graph", response_model=RelationGraph)
async def get_relation_graph(
    trench_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    nodes = []
    edges = []

    trenches_query = db.query(Trench)
    if trench_id:
        trenches_query = trenches_query.filter(Trench.id == trench_id)
    trenches = trenches_query.all()

    for trench in trenches:
        nodes.append(RelationNode(
            id=f"trench_{trench.id}",
            label=f"探方: {trench.code}",
            type="trench",
            data={"location": trench.location, "status": trench.status.value}
        ))
        for stratum in trench.strata:
            nodes.append(RelationNode(
                id=f"stratum_{stratum.id}",
                label=f"地层: {stratum.code}",
                type="stratum",
                data={"soil_type": stratum.soil_type, "age": stratum.estimated_age, "order": stratum.order_index}
            ))
            edges.append(RelationEdge(
                source=f"trench_{trench.id}",
                target=f"stratum_{stratum.id}",
                label="包含"
            ))
            for artifact in stratum.artifacts:
                nodes.append(RelationNode(
                    id=f"artifact_{artifact.id}",
                    label=f"出土物: {artifact.code}",
                    type="artifact",
                    data={"category": artifact.category, "status": artifact.status.value}
                ))
                edges.append(RelationEdge(
                    source=f"stratum_{stratum.id}",
                    target=f"artifact_{artifact.id}",
                    label="出土于"
                ))

    return RelationGraph(nodes=nodes, edges=edges)


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {
        "trenches": db.query(Trench).count(),
        "strata": db.query(Stratum).count(),
        "artifacts": db.query(Artifact).count(),
        "users": db.query(User).count()
    }
