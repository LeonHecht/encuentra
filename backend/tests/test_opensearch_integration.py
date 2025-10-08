# backend/tests/test_opensearch_integration.py
from opensearchpy import OpenSearch
import pytest

@pytest.mark.opensearch
def test_search_with_ephemeral(os_ephemeral_index):
    c = OpenSearch([{"host":"localhost","port":9200}], http_compress=True, verify_certs=False)
    idx = os_ephemeral_index

    docs = [
        {"id":"1","title":"Sentencia penal","text":"Sala de lo Penal resolvió..."},
        {"id":"2","title":"Habeas corpus","text":"Sala de lo Constitucional improcedente..."},
    ]
    for d in docs:
        c.index(index=idx, id=d["id"], body=d)  # ES7 style: body=
    c.indices.refresh(index=idx)

    res = c.search(index=idx, body={
        "query": {"multi_match": {"query": "Sala de lo Penal", "fields": ["title^2","text"], "operator": "and"}}
    })
    assert res["hits"]["hits"]
