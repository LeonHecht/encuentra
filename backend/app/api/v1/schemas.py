from pydantic import BaseModel, Field
from typing import List, Literal


class SearchRequest(BaseModel):
    """Parameters for a search request."""
    query: str
    top_k: int = 30
    use_transformer: bool = False


class SearchResult(BaseModel):
    """A single search hit."""
    id: str
    score: float
    title: str | None = Field(default=None)   # <- allow None
    case_year: int | None = None
    snippet: str | None = None
    download_url: str | None = None
    metadata_status: Literal["missing", "pending", "ready", "failed"] = "missing"
    metadata: dict | None = None


class CaseMetadataResponse(BaseModel):
    """Cached enrichment metadata for a case."""
    space: str
    doc_id: str
    status: Literal["missing", "pending", "ready", "failed"]
    metadata: dict | None = None
    error: str | None = None


class SearchResponse(BaseModel):
    """
    Response for `/search`.

    Parameters
    ----------
    query_log_id : str | None
        The ID of the logged query in the database.
    results : List[SearchResult]
        The list of retrieved documents.
    """
    query_log_id: str | None = Field(None, description="ID of the SearchQueryLog entry")
    results: List[SearchResult] = Field(..., description="Retrieved documents")


class SearchFeedbackRequest(BaseModel):
    """User feedback for a single displayed search result."""
    query_log_id: str | None = None
    query_text: str = Field(..., min_length=1)
    space: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=50)
    year_filter: int | None = Field(default=None, ge=1800, le=2100)
    doc_id: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    score: float | None = None
    title: str | None = None
    snippet: str | None = None
    feedback: Literal["positive", "negative"]
    reason: str | None = None
    metadata: dict | None = None


class SearchFeedbackResponse(BaseModel):
    id: str | None = None
    saved: bool = True


class ChatFeedbackMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatFeedbackRequest(BaseModel):
    """User feedback for a single assistant chat message."""
    chat_id: str = Field(..., min_length=1)
    assistant_message_id: str = Field(..., min_length=1)
    space: str | None = None
    previous_user_message: str | None = None
    previous_messages: list[ChatFeedbackMessage] = Field(default_factory=list)
    assistant_response: str = Field(..., min_length=1)
    citations: list[dict] = Field(default_factory=list)
    feedback: Literal["positive", "negative"]
    feedback_text: str | None = None
    metadata: dict | None = None


class ChatFeedbackResponse(BaseModel):
    id: str | None = None
    saved: bool = True

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    first_name: str | None = None
    last_name: str | None = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str


class UserInfo(BaseModel):
    username: str
    first_name: str
    last_name: str

class SpaceCreateRequest(BaseModel):
    name: str
