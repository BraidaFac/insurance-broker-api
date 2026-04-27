import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Client, Message, Policy, Quote, QuoteCreate, QuotePublic, QuotesPublic, QuoteUpdate

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/", response_model=QuotesPublic)
def read_quotes(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """Retrieve all quotes."""
    count = session.exec(select(func.count()).select_from(Quote)).one()
    quotes = session.exec(select(Quote).offset(skip).limit(limit)).all()
    return QuotesPublic(data=[QuotePublic.model_validate(q) for q in quotes], count=count)


@router.get("/{id}", response_model=QuotePublic)
def read_quote(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """Get quote by ID."""
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.post("/", response_model=QuotePublic)
def create_quote(*, session: SessionDep, current_user: CurrentUser, quote_in: QuoteCreate) -> Any:
    """Create new quote. Validates that client and policy exist."""
    if not session.get(Client, quote_in.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    if not session.get(Policy, quote_in.policy_id):
        raise HTTPException(status_code=404, detail="Policy not found")

    quote = Quote.model_validate(quote_in)
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.patch("/{id}", response_model=QuotePublic)
def update_quote(
    *, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, quote_in: QuoteUpdate
) -> Any:
    """Update quote status or premium."""
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote.sqlmodel_update(quote_in.model_dump(exclude_unset=True))
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.delete("/{id}")
def delete_quote(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    """Delete a quote."""
    quote = session.get(Quote, id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    session.delete(quote)
    session.commit()
    return Message(message="Quote deleted successfully")
