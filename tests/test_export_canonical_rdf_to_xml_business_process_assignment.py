from pathlib import Path

from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.config import GRAPHDB_BASE_URL
from archimate_adapter.services.export_canonical_rdf_to_xml import (
    ExportCanonicalRdfToXmlService,
)
from archimate_adapter.services.import_xml_to_canonical_rdf import (
    ImportXmlToCanonicalRdfService,
)


def test_export_canonical_rdf_to_xml_includes_business_process_and_assignment(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-business-process-assignment"
    output_path = tmp_path / "exported-business-process-assignment.xml"

    client = GraphDBClient(
        base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
    )

    import_service = ImportXmlToCanonicalRdfService(
        graphdb_base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    export_service = ExportCanonicalRdfToXmlService(
        graphdb_base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        import_service.import_from_file("tests/fixtures/xml/business_process_assignment.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="BusinessActor"' in xml_text
        assert 'xsi:type="BusinessProcess"' in xml_text
        assert 'xsi:type="Assignment"' in xml_text

        assert 'identifier="actor-1"' in xml_text
        assert 'identifier="process-1"' in xml_text
        assert 'identifier="rel-2"' in xml_text

        assert 'source="actor-1"' in xml_text
        assert 'target="process-1"' in xml_text

        assert "Case Worker" in xml_text
        assert "Handle Application" in xml_text
        assert "is responsible for" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass
