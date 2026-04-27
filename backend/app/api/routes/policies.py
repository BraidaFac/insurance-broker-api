import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    PoliciesPublic,
    Policy,
    PolicyCreate,
    PolicyPublic,
    PolicySearchResult,
    PolicyUpdate,
)
from app.services.embeddings import embed_text
from app.services.search import semantic_search

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("/search/semantic", response_model=list[PolicySearchResult])
def search_policies_semantic(
    session: SessionDep,
    current_user: CurrentUser,
    q: str,
    k: int = 5,
) -> Any:
    """
    Semantic search over policies using pgvector cosine distance.
    Embeds the query and returns the top-k most similar policies.
    """
    return semantic_search(session=session, query=q, k=k)


@router.get("/", response_model=PoliciesPublic)
def read_policies(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve all policies."""
    count = session.exec(select(func.count()).select_from(Policy)).one()
    policies = session.exec(select(Policy).offset(skip).limit(limit)).all()
    return PoliciesPublic(data=[PolicyPublic.model_validate(p) for p in policies], count=count)


@router.get("/{id}", response_model=PolicyPublic)
def read_policy(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """Get policy by ID."""
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("/", response_model=PolicyPublic)
def create_policy(*, session: SessionDep, current_user: CurrentUser, policy_in: PolicyCreate) -> Any:
    """Create new policy."""
    policy = Policy.model_validate(policy_in)
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.patch("/{id}", response_model=PolicyPublic)
def update_policy(
    *, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, policy_in: PolicyUpdate
) -> Any:
    """Update a policy."""
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.sqlmodel_update(policy_in.model_dump(exclude_unset=True))
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.delete("/{id}")
def delete_policy(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    """Delete a policy."""
    policy = session.get(Policy, id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    session.delete(policy)
    session.commit()
    return Message(message="Policy deleted successfully")


@router.post("/reindex", response_model=Message)
def reindex_policies(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Generate and store embeddings for all policies using text-embedding-3-small.
    Safe to call multiple times — overwrites existing embeddings.
    """
    policies = session.exec(select(Policy)).all()
    if not policies:
        raise HTTPException(status_code=404, detail="No policies found to index")

    for policy in policies:
        embedding = embed_text(policy.description)
        policy.embedding = embedding  # type: ignore[assignment]
        session.add(policy)

    session.commit()
    return Message(message=f"Reindexed {len(policies)} policies successfully")
