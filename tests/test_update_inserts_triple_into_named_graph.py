from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.config import GRAPHDB_BASE_URL


def test_update_inserts_triple_into_named_graph():
    client = GraphDBClient(
        base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
    )

    graph_iri = "https://example.org/graph/test-import"

    try:
        client.update(f"""
        INSERT DATA {{
          GRAPH <{graph_iri}> {{
            <https://example.org/s> <https://example.org/p> <https://example.org/o> .
          }}
        }}
        """)

        result = client.ask(f"""
        ASK {{
          GRAPH <{graph_iri}> {{
            <https://example.org/s> <https://example.org/p> <https://example.org/o> .
          }}
        }}
        """)

        assert result is True

    finally:
        try:
            client.update(f"""
            CLEAR GRAPH <{graph_iri}>
            """)
        except GraphDBClientError:
            pass
