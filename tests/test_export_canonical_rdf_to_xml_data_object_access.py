from pathlib import Path

from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.services.export_canonical_rdf_to_xml import (
    ExportCanonicalRdfToXmlService,
)
from archimate_adapter.services.import_xml_to_canonical_rdf import (
    ImportXmlToCanonicalRdfService,
)


def test_export_canonical_rdf_to_xml_includes_data_object_and_access(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-data-object-access"
    output_path = tmp_path / "exported-data-object-access.xml"

    client = GraphDBClient(
        base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
    )

    import_service = ImportXmlToCanonicalRdfService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    export_service = ExportCanonicalRdfToXmlService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        import_service.import_from_file("tests/fixtures/xml/data_object_access.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="ApplicationComponent"' in xml_text
        assert 'xsi:type="DataObject"' in xml_text
        assert 'xsi:type="Access"' in xml_text

        assert 'identifier="app-1"' in xml_text
        assert 'identifier="data-1"' in xml_text
        assert 'identifier="rel-4"' in xml_text

        assert 'source="app-1"' in xml_text
        assert 'target="data-1"' in xml_text

        assert "Case App" in xml_text
        assert "Case Record" in xml_text
        assert "accesses" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass