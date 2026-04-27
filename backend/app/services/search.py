from sqlmodel import Session, text

from app.models import PolicySearchResult
from app.services.embeddings import embed_text


def semantic_search(session: Session, query: str, k: int = 5) -> list[PolicySearchResult]:
    """
    Embed the query and run a cosine-distance nearest-neighbour search
    using pgvector's <=> operator. Returns top-k policies with scores.
    """
    query_embedding = embed_text(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    stmt = text(
        """
        SELECT id, product_type, insurer, sum_insured_nzd, description,
               (embedding <=> CAST(:embedding AS vector)) AS distance
        FROM policy
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT :k
        """
    )
    rows = session.exec(stmt, params={"embedding": embedding_str, "k": k}).mappings().all()  # type: ignore[call-overload]

    return [
        PolicySearchResult(
            id=row["id"],
            product_type=row["product_type"],
            insurer=row["insurer"],
            sum_insured_nzd=row["sum_insured_nzd"],
            description=row["description"],
            distance=float(row["distance"]),
        )
        for row in rows
    ]
