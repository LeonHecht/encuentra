""" Run the following to test OpenSearch integration (requires local OpenSearch instance):

SEARCH_BACKEND=opensearch PYTHONPATH=. pytest -v -m opensearch
"""

from backend.app.services.opensearch import opensearch_engine
from opensearchpy import OpenSearch
import pytest

@pytest.mark.opensearch
def test_opensearch_index_and_search(tmp_path):
    docs = [
        {"id": "1", "title": "Sentencia penal", "text": "La Sala de lo Penal resolvió..."},
        {"id": "2", "title": "Habeas corpus", "text": "La Sala de lo Constitucional declaró improcedente..."},
    ]

    client: OpenSearch = opensearch_engine._get_client()
    index = "supreme_court"

    client.indices.delete(index=index, ignore=[400, 404])
    client.indices.create(index=index, body={
        "mappings": {"properties": {
            "id": {"type": "keyword"},
            "title": {"type": "text"},
            "text": {"type": "text"}
        }}
    })

    for d in docs:
        client.index(index=index, id=d["id"], body=d)  # 👈 use body=

    client.indices.refresh(index=index)

    # If your search() builds index from prefix+space, either:
    #   results = opensearch_engine.search("Sala de lo Penal", space="test")
    # or call the client directly:
    res = client.search(index=index, body={
        "query": {"multi_match": {"query": "Sala de lo Penal", "fields": ["title^2", "text"]}}
    })
    hits = res["hits"]["hits"]
    assert any("Penal" in (h["_source"].get("title","") + " " + h["_source"].get("text","")) for h in hits)


def test_search_with_ephemeral(os_ephemeral_index):
    c = OpenSearch([{"host":"localhost","port":9200}], http_compress=True, verify_certs=False)
    index_alias = os_ephemeral_index

    docs = [
        {"id": "1", "title": "Sentencia penal", "text": "Sala de lo Penal resolvió..."},
        {"id": "2", "title": "Habeas corpus", "text": "Sala de lo Constitucional improcedente..."},
    ]
    for d in docs:
        c.index(index=index_alias, id=d["id"], body=d)
    c.indices.refresh(index=index_alias)

    res = c.search(index=index_alias, body={
        "query": {"multi_match": {"query": "Sala de lo Penal", "fields": ["title^2","text"], "operator": "and"}}
    })
    assert res["hits"]["hits"]
