import traceback

from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
# from typing import List, Dict
from ..schemas import CaseMetadataResponse, SearchResponse, SearchResult
from backend.app.services.search import search_engine
from backend.app.dependencies import get_current_user
from backend.app.services.auth import get_accessible_spaces, UserData
from backend.app.core.config import settings
from backend.app.services import case_metadata


router = APIRouter()

@router.get("/spaces")
def list_spaces(user: UserData = Depends(get_current_user)):
    """Return available search spaces for the current user."""
    return {"spaces": get_accessible_spaces(user)}

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=50),
    space: str = Query(..., min_length=1, description="Contexto: supreme_court|my_uploads|<other>"),
    background_tasks: BackgroundTasks = None,
    user: UserData = Depends(get_current_user),
):
    print(f"Received search query: '{q}' in space '{space}' with top_k={top_k}", flush=True)
    if space not in get_accessible_spaces(user):
        raise HTTPException(403, detail="Space not accessible")
    try:
        if not search_engine.has_space(space):
            raise HTTPException(400, detail=f"Unknown space '{space}'")
        hits = search_engine.search(q, top_k, space)
        doc_ids = [str(hit.get("id")) for hit in hits if hit.get("id")]
        metadata_rows = case_metadata.get_metadata_rows(space, doc_ids)
        scheduled = 0
        for hit in hits:
            doc_id = str(hit.get("id") or "")
            row = metadata_rows.get(doc_id)
            status = case_metadata.normalize_status(row)
            hit["metadata_status"] = status
            hit["metadata"] = row.get("metadata") if row and status == "ready" else None

            if settings.CASE_METADATA_AUTO_ENRICH and scheduled < settings.CASE_METADATA_TOP_K and status in ("missing", "pending", "failed"):
                try:
                    should_enqueue = case_metadata.upsert_pending(space, doc_id, row)
                except Exception as exc:
                    print(f"[case_metadata] Failed to enqueue {space}/{doc_id}: {exc}", flush=True)
                    should_enqueue = False

                if should_enqueue:
                    hit["metadata_status"] = "pending"
                    if background_tasks is not None:
                        background_tasks.add_task(
                            case_metadata.enrich_case_metadata,
                            space,
                            doc_id,
                            q,
                            hit.get("snippet"),
                        )
                    scheduled += 1
        results = [SearchResult(**hit) for hit in hits]
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Search failed for query '{q}' in space '{space}': {exc}", flush=True)
        traceback.print_exc()
        raise HTTPException(503, detail="Search backend unavailable") from exc
    return SearchResponse(query_log_id=1, results=results)


@router.get("/cases/{space}/{doc_id}/metadata", response_model=CaseMetadataResponse)
def get_case_metadata(
    space: str,
    doc_id: str,
    user: UserData = Depends(get_current_user),
):
    if space not in get_accessible_spaces(user):
        raise HTTPException(403, detail="Space not accessible")
    row = case_metadata.get_metadata_row(space, doc_id)
    return CaseMetadataResponse(**case_metadata.row_to_response(space, doc_id, row))


@router.get("/case-metadata", response_model=CaseMetadataResponse)
def get_case_metadata_by_query(
    space: str = Query(..., min_length=1),
    doc_id: str = Query(..., min_length=1),
    user: UserData = Depends(get_current_user),
):
    return get_case_metadata(space=space, doc_id=doc_id, user=user)

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
