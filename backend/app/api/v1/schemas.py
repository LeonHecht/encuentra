from pydantic import BaseModel, Field
from typing import List


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
    snippet: str | None = None
    download_url: str | None = None


class SearchResponse(BaseModel):
    """
    Response for `/search`.

    Parameters
    ----------
    query_log_id : int
        The ID of the logged query in the database.
    results : List[SearchResult]
        The list of retrieved documents.
    """
    query_log_id: int = Field(..., description="ID of the QueryLog entry")
    results: List[SearchResult] = Field(..., description="Retrieved documents")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    space: str = Field("supreme_court", description="Which corpus to use")
    use_transformer: bool = False            # for later

class Citation(BaseModel):
    doc_id: str
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]