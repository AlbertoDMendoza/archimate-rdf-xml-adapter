from pathlib import Path

from archimate_adapter.services.export_canonical_rdf_to_xml import (
    ExportCanonicalRdfToXmlService,
)


def test_export_canonical_rdf_to_xml_creates_expected_file(tmp_path: Path) -> None:
    output_path = tmp_path / "exported-from-graphdb.xml"

    service = ExportCanonicalRdfToXmlService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri="https://example.org/graph/model",
    )

    service.export_to_file(str(output_path))

    assert output_path.exists()

    xml_text = output_path.read_text(encoding="utf-8")

    assert "<elements>" in xml_text
    assert "<relationships>" in xml_text
    assert "ApplicationComponent" in xml_text
    assert "BusinessActor" in xml_text
    assert "Serving" in xml_text