# backend/tests/conftest.py
import os, time, random, string, pytest
from opensearchpy import OpenSearch

def _rand(n=6): 
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

@pytest.fixture(scope="function")
def os_ephemeral_index(monkeypatch):
    # use a dedicated test prefix/alias to avoid collisions
    base_prefix = os.getenv("OPENSEARCH_INDEX_PREFIX", "sv")
    test_prefix = f"{base_prefix}-test"        # e.g. sv-test
    alias = test_prefix                        # alias clients will query
    index = f"{test_prefix}-{int(time.time()*1000)}-{_rand()}"  # concrete build index

    client = OpenSearch(
        [{"host":"localhost","port":9200}],
        http_compress=True,
        verify_certs=False,
    )

    # minimal mapping (swap in your spanish analyzer if desired)
    body = {
        "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
        "mappings": {"properties": {
            "id": {"type":"keyword"},
            "title": {"type":"text"},
            "text": {"type":"text"},
        }},
    }
    client.indices.create(index=index, body=body, ignore=400)

    # point alias -> new index (remove any previous)
    actions = []
    if client.indices.exists_alias(name=alias):
        olds = list(client.indices.get_alias(name=alias).keys())
        for o in olds:
            actions.append({"remove": {"index": o, "alias": alias}})
    actions.append({"add": {"index": index, "alias": alias}})
    client.indices.update_aliases(body={"actions": actions})   # <-- body=

    # ensure the app uses this prefix during the test (if code builds names via prefix)
    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "OPENSEARCH_INDEX_PREFIX", test_prefix)

    try:
        yield alias   # return the alias to tests
    finally:
        # cleanup: drop alias and index
        client.indices.delete_alias(index="_all", name=alias, ignore=[404])
        client.indices.delete(index=index, ignore=[404])
