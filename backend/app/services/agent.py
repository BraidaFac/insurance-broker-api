import json

from openai import OpenAI
from sqlmodel import Session

from app.core.config import settings
from app.services.embeddings import get_openai_client
from app.services.search import semantic_search

SYSTEM_PROMPT = """You are an expert insurance broker assistant for a New Zealand commercial insurance platform.
Your job is to help brokers find the most suitable policies for their clients.
When answering questions, always use the search_policies_semantic tool to find relevant policies,
then provide a clear, grounded recommendation citing the specific policies by name and insurer."""


def ask_agent(question: str, session: Session) -> str:
    """
    Single round-trip LLM agent with tool calling.
    The model decides to call search_policies_semantic, we execute it,
    then the model produces a final natural-language answer.
    """
    client: OpenAI = get_openai_client()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_policies_semantic",
                "description": (
                    "Search the policy database using natural language. "
                    "Returns the top-k most relevant insurance policies with similarity scores."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language description of the coverage needed",
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of policies to return (default 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    # First call — let the model decide whether to use tools
    response = client.chat.completions.create(
        model=settings.AGENT_MODEL,
        messages=messages,  # type: ignore[arg-type]
        tools=tools,  # type: ignore[arg-type]
        tool_choice="auto",
    )

    assistant_message = response.choices[0].message

    # If the model called a tool, execute it and send results back
    if assistant_message.tool_calls:
        messages.append(assistant_message)  # type: ignore[arg-type]

        for tool_call in assistant_message.tool_calls:
            if tool_call.function.name == "search_policies_semantic":
                args = json.loads(tool_call.function.arguments)
                results = semantic_search(
                    session=session,
                    query=args["query"],
                    k=args.get("k", 5),
                )
                tool_result = [
                    {
                        "id": str(r.id),
                        "product_type": r.product_type,
                        "insurer": r.insurer,
                        "sum_insured_nzd": r.sum_insured_nzd,
                        "description": r.description,
                        "distance": r.distance,
                    }
                    for r in results
                ]
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result),
                    }
                )

        # Second call — model produces final answer grounded in search results
        final_response = client.chat.completions.create(
            model=settings.AGENT_MODEL,
            messages=messages,  # type: ignore[arg-type]
        )
        return final_response.choices[0].message.content or ""

    return assistant_message.content or ""
