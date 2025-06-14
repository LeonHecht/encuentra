from fastapi import APIRouter, Query, HTTPException
# from typing import List, Dict
from ..schemas import SearchResponse, SearchResult
from app.services.bm25 import bm25_engine


router = APIRouter()

@router.get("/spaces")
def list_spaces():
    """Return available search spaces."""
    return {"spaces": list(bm25_engine.bm25_models.keys())}

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=50),
    space: str = Query(..., min_length=1, description="Contexto: supreme_court|my_uploads|<other>")
):
    print(f"Received search query: '{q}' in space '{space}' with top_k={top_k}")
    if space not in bm25_engine.bm25_models:
        raise HTTPException(400, detail=f"Unknown space '{space}'")
    hits = bm25_engine.search(q, top_k, space)
    results = [SearchResult(**hit) for hit in hits]
    # TODO: log query with space
    return SearchResponse(query_log_id=1, results=results)

# @router.post("/search", response_model=SearchResponse, summary="Run a BM25 or transformer search")
# def search(request: Request, req: SearchRequest = Body(..., description="Your search parameters")) -> SearchResponse:
#     """
#     Execute a search and log the query.

#     1. Validates non-empty query.
#     2. Captures client IP, country, and city.
#     3. Inserts a QueryLog row and retrieves its ID.
#     4. Runs either BM25 or transformer search.
#     5. Returns the log ID along with the hits.
#     """
#     if not req.query.strip():
#         raise HTTPException(status_code=400, detail="Query must not be empty")
    
#     client_ip = request.client.host or "Unknown"
#     country   = country_from_ip(client_ip) or "Unknown"
#     city      = city_from_ip(client_ip) or "Unknown"
    
#     # 1) Log the search
#     with Session(engine) as sess:
#         log = QueryLog(
#             client_ip=client_ip,
#             country=country,
#             city=city,
#             mode="semantica" if req.use_transformer else "exacta",
#             query=req.query.strip(),
#         )
#         sess.add(log)
#         sess.commit()
#         sess.refresh(log)  # populates log.id

#     # 2) Run the actual search  
#     if req.use_transformer:
#         hits = transformer_search(req.query, top_k=req.top_k)
#     else:
#         # existing BM25 search returns full results
#         hits = bm25_search(req.query, top_k=req.top_k)
    
#     # 3) Return both the log ID and the results
#     return SearchResponse(query_log_id=log.id, results=hits)