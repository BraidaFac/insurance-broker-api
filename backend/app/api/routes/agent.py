from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models import AgentAsk, AgentResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/ask", response_model=AgentResponse)
def ask_agent_endpoint(
    *, session: SessionDep, current_user: CurrentUser, body: AgentAsk
) -> Any:
    """
    LLM agent endpoint. Accepts a natural-language question, uses GPT-4o via OpenRouter
    with tool calling to search policies semantically, and returns a grounded answer.
    """
    from app.services.agent import ask_agent  # lazy import to avoid startup errors if key not set

    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    answer = ask_agent(question=body.question, session=session)
    return AgentResponse(answer=answer)
