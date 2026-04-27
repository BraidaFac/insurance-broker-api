import enum
import uuid
from typing import Any

from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel


class ProductType(str, enum.Enum):
    public_liability = "public_liability"
    professional_indemnity = "professional_indemnity"
    cyber = "cyber"
    business_interruption = "business_interruption"


class QuoteStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"


# ── Client ──────────────────────────────────────────────────────────────────

class ClientBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=255)
    annual_turnover_nzd: float
    notes: str | None = Field(default=None)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = Field(default=None, min_length=1, max_length=255)
    annual_turnover_nzd: float | None = None
    notes: str | None = None


class Client(ClientBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quotes: list["Quote"] = Relationship(back_populates="client", cascade_delete=True)


class ClientPublic(ClientBase):
    id: uuid.UUID


class ClientsPublic(SQLModel):
    data: list[ClientPublic]
    count: int


# ── Policy ──────────────────────────────────────────────────────────────────

class PolicyBase(SQLModel):
    product_type: ProductType
    insurer: str = Field(min_length=1, max_length=255)
    sum_insured_nzd: float
    description: str


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(SQLModel):
    product_type: ProductType | None = None
    insurer: str | None = Field(default=None, min_length=1, max_length=255)
    sum_insured_nzd: float | None = None
    description: str | None = None


class Policy(PolicyBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # embedding stored as pgvector vector(1536); excluded from public schemas
    embedding: Any = Field(default=None, sa_column=Column("embedding", nullable=True))
    quotes: list["Quote"] = Relationship(back_populates="policy", cascade_delete=True)


class PolicyPublic(PolicyBase):
    id: uuid.UUID


class PoliciesPublic(SQLModel):
    data: list[PolicyPublic]
    count: int


class PolicySearchResult(PolicyPublic):
    distance: float


# ── Quote ───────────────────────────────────────────────────────────────────

class QuoteBase(SQLModel):
    premium_nzd: float
    status: QuoteStatus = QuoteStatus.draft


class QuoteCreate(QuoteBase):
    client_id: uuid.UUID
    policy_id: uuid.UUID


class QuoteUpdate(SQLModel):
    premium_nzd: float | None = None
    status: QuoteStatus | None = None


class Quote(QuoteBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_id: uuid.UUID = Field(foreign_key="client.id", nullable=False, ondelete="CASCADE")
    policy_id: uuid.UUID = Field(foreign_key="policy.id", nullable=False, ondelete="CASCADE")
    client: Client | None = Relationship(back_populates="quotes")
    policy: Policy | None = Relationship(back_populates="quotes")


class QuotePublic(QuoteBase):
    id: uuid.UUID
    client_id: uuid.UUID
    policy_id: uuid.UUID


class QuotesPublic(SQLModel):
    data: list[QuotePublic]
    count: int


# ── Agent ───────────────────────────────────────────────────────────────────

class AgentAsk(SQLModel):
    question: str


class AgentResponse(SQLModel):
    answer: str
