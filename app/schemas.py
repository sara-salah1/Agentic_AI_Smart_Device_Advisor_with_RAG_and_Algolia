
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any

Role = Literal["user", "assistant", "system"]


class Message(BaseModel):
    role: Role
    content: str


class RecommendRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Single-turn query. If provided, messages can be omitted.")
    messages: Optional[List[Message]] = Field(default=None, description="Multi-turn conversation. The last user message is considered the active intent.")
    top_n: int = Field(default=5, ge=1, le=20)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class Hit(BaseModel):
    title: str
    objectID: str
    price: Optional[float] = None
    url: Optional[str] = None
    brand: Optional[str] = None
    categories: Optional[list[str]] = None
    image: Optional[str] = None
    attributes: Optional[dict] = None
    _raw: Optional[dict] = None


class Recommendation(BaseModel):
    title: str
    price: Optional[float] = None
    url: Optional[str] = None
    score: float
    reasons: List[str] = []
    citations: List[str] = []


class RecommendResponse(BaseModel):
    recommendations: List[Recommendation]
    clarifying_questions: List[str] = []
    used_fallback_generator: bool = False
    debug: Optional[dict[str, Any]] = None
