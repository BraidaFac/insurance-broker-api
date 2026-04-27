"""
Smoke tests for GET /policies/search/semantic.

These tests verify that the endpoint responds correctly and returns
results in the expected shape. They do NOT call OpenRouter — embed_text
is mocked to return a fixed vector so tests run offline and cheaply.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Policy, ProductType

# A fixed 1536-dim vector used as a stand-in for a real embedding.
# All values identical → cosine distance between this and itself is 0 (perfect match).
_DUMMY_VECTOR: list[float] = [0.1] * 1536


def test_semantic_search_returns_200_and_list(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Endpoint must return HTTP 200 and a JSON list regardless of whether
    any policies have embeddings stored.
    """
    with patch("app.services.search.embed_text", return_value=_DUMMY_VECTOR):
        response = client.get(
            f"{settings.API_V1_STR}/policies/search/semantic",
            params={"q": "cyber liability for small business", "k": 5},
            headers=superuser_token_headers,
        )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_semantic_search_results_have_distance_sorted_ascending(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """
    Results must include a 'distance' field and be ordered
    from closest (lowest distance) to furthest (highest distance).
    """
    # Insert two policies with known embeddings directly into the DB.
    # Using slightly different vectors so their distances to the query differ.
    policy_close = Policy(
        product_type=ProductType.cyber,
        insurer="Smoke Test Insurer A",
        sum_insured_nzd=1_000_000,
        description="Cyber coverage smoke test policy — close match",
        embedding=[0.1] * 1536,   # identical to query vector → distance ≈ 0
    )
    policy_far = Policy(
        product_type=ProductType.public_liability,
        insurer="Smoke Test Insurer B",
        sum_insured_nzd=500_000,
        description="Public liability smoke test policy — far match",
        embedding=[-0.1] * 1536,  # opposite direction → distance ≈ 1
    )
    db.add(policy_close)
    db.add(policy_far)
    db.commit()

    try:
        with patch("app.services.search.embed_text", return_value=_DUMMY_VECTOR):
            response = client.get(
                f"{settings.API_V1_STR}/policies/search/semantic",
                params={"q": "cyber", "k": 10},
                headers=superuser_token_headers,
            )

        assert response.status_code == 200
        results = response.json()

        # Filter to only our test policies so other DB state doesn't interfere.
        test_results = [
            r for r in results
            if r["insurer"] in ("Smoke Test Insurer A", "Smoke Test Insurer B")
        ]

        assert len(test_results) == 2, "Both test policies must appear in results"
        assert all("distance" in r for r in test_results), "Every result must have a distance score"

        distances = [r["distance"] for r in results  # check global ordering, not just ours
                     if "distance" in r]
        assert distances == sorted(distances), "Results must be sorted by distance ascending"

    finally:
        # Always clean up test data regardless of assertion outcome.
        db.delete(policy_close)
        db.delete(policy_far)
        db.commit()
