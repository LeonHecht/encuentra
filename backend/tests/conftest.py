# backend/tests/conftest.py
import os, time, random, string, pytest
from opensearchpy import OpenSearch

def _rand(n=6): return ''.join(random.choices(string.ascii_lowercase+string.digits, k=n))

@pytest.fixture(scope="function")
def os_ephemeral_index(monkeypatch):
    # Use a dedicated test prefix
    prefix = os.getenv("OPENSEARCH_INDEX_PREFIX", "sv-test")
    alias  = f"{prefix}"          # e.g., 'sv-test'
    index  = f"{prefix}-{int(time.time()*1000)}-{_rand()}"  # e.g., 'sv-test-173...-ab12cd'

    client = OpenSearch([{"host":"localhost","port":9200}], http_compress=True, verify_certs=False)

    # Create index with minimal mapping (or your spanish_legal analyzer)
    body = {
        "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
        "mappings": {"properties": {
            "id": {"type":"keyword"},
            "title": {"type":"text"},
            "text": {"type":"text"}
        }}
    }
    client.indices.create(index=index, body=body, ignore=400)

    # Point alias to this fresh index (remove previous alias targets if any)
    actions=[]
    if client.indices.exists_alias(name=alias):
        olds = client.indices.get_alias(name=alias).keys()
        for o in olds:
            actions.append({"remove": {"index": o, "alias": alias}})
    actions.append({"add": {"index": index, "alias": alias}})
    client.indices.update_aliases({"actions": actions})

    # Ensure your app uses the same prefix during this test
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "OPENSEARCH_INDEX_PREFIX", prefix)

    yield alias  # or yield (alias, index) if you prefer

    # Cleanup
    try:
        client.indices.delete_alias(index="_all", name=alias, ignore=[404])
        client.indices.delete(index=index, ignore=[404])
    except Exception:
        pass
