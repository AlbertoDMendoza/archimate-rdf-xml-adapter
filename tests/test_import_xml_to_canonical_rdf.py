import pytest

from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.namespaces import ARCHIMATE_NS, EX_NS, RDF_NS
from archimate_adapter.services.import_xml_to_canonical_rdf import (
    ImportXmlToCanonicalRdfService,
)


def test_import_from_file_inserts_phase1_model_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import"

    client = GraphDBClient(
        base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
    )

    service = ImportXmlToCanonicalRdfService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    app_iri = f"{EX_NS}app-1"
    actor_iri = f"{EX_NS}actor-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file("tests/fixtures/xml/exported-from-graphdb.xml")

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{app_iri}> rdf:type archimate:ApplicationComponent .
                <{actor_iri}> rdf:type archimate:BusinessActor .
                <{app_iri}> archimate:serving <{actor_iri}> .
                << <{app_iri}> archimate:serving <{actor_iri}> >>
                  archimate:identifier "rel-1" .
              }}
            }}
            """
        )

        assert result is True

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass