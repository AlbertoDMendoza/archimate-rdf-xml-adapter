from pathlib import Path

import pytest

from archimate_adapter.dto.model import ElementDTO, ModelDTO, RelationshipDTO
from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.namespaces import ARCHIMATE_NS, EX_NS, RDF_NS
from archimate_adapter.services.export_canonical_rdf_to_xml import (
    ExportCanonicalRdfToXmlService,
)
from archimate_adapter.services.import_xml_to_canonical_rdf import (
    ImportXmlToCanonicalRdfService,
)
from archimate_adapter.services.xml_to_rdf import (
    ElementTypeRegistry,
    RelationshipTypeRegistry,
    build_canonical_import_sparql,
)
from archimate_adapter.xml.parser import parse_archimate_model_string


def test_parse_model_with_application_interface_and_composition():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Demo model</name>
      <elements>
        <element identifier="app-1" xsi:type="ApplicationComponent">
          <name xml:lang="en">Case App</name>
          <documentation xml:lang="en">Application component.</documentation>
        </element>
        <element identifier="appi-1" xsi:type="ApplicationInterface">
          <name xml:lang="en">Case Interface</name>
          <documentation xml:lang="en">Application interface for exposing the component.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-6"
                      xsi:type="Composition"
                      source="app-1"
                      target="appi-1">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Application component is composed of application interface.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 2
    assert len(model.relationships) == 1

    app = model.get_element("app-1")
    assert app.xml_type == "ApplicationComponent"
    assert app.name == "Case App"
    assert app.documentation == "Application component."

    appi = model.get_element("appi-1")
    assert appi.xml_type == "ApplicationInterface"
    assert appi.name == "Case Interface"
    assert appi.documentation == "Application interface for exposing the component."

    rel = model.relationships[0]
    assert rel.identifier == "rel-6"
    assert rel.xml_type == "Composition"
    assert rel.exchange_type == "Composition"
    assert rel.source_id == "app-1"
    assert rel.target_id == "appi-1"
    assert rel.name == "contains"
    assert rel.documentation == "Application component is composed of application interface."


def test_build_canonical_import_sparql_with_application_interface_and_composition():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="app-1",
            xml_type="ApplicationComponent",
            name="Case App",
            documentation="Application component.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appi-1",
            xml_type="ApplicationInterface",
            name="Case Interface",
            documentation="Application interface for exposing the component.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-6",
            xml_type="Composition",
            exchange_type="Composition",
            source_id="app-1",
            target_id="appi-1",
            name="contains",
            documentation="Application component is composed of application interface.",
        )
    )

    element_registry = ElementTypeRegistry.from_yaml(
        "src/archimate_adapter/mapping/element_types.yaml"
    )
    relationship_registry = RelationshipTypeRegistry.from_yaml(
        "src/archimate_adapter/mapping/relationship_types.yaml"
    )

    sparql = build_canonical_import_sparql(
        model=model,
        element_registry=element_registry,
        relationship_registry=relationship_registry,
    )

    assert "https://purl.org/archimate#ApplicationComponent" in sparql
    assert "https://purl.org/archimate#ApplicationInterface" in sparql
    assert "https://purl.org/archimate#composition" in sparql
    assert 'archimate:identifier "rel-6"' in sparql
    assert (
        "<< ex:app-1 <https://purl.org/archimate#composition> ex:appi-1 >>"
        in sparql
    )
    assert (
        "ex:app-1 <https://purl.org/archimate#composition> ex:appi-1 ."
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_application_interface_and_composition_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-application-interface-composition"

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
    appi_iri = f"{EX_NS}appi-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file("tests/fixtures/xml/application_interface_composition.xml")

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{app_iri}> rdf:type archimate:ApplicationComponent .
                <{appi_iri}> rdf:type archimate:ApplicationInterface .
                <{app_iri}> archimate:composition <{appi_iri}> .
                << <{app_iri}> archimate:composition <{appi_iri}> >>
                  archimate:identifier "rel-6" .
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


def test_export_canonical_rdf_to_xml_includes_application_interface_and_composition(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-application-interface-composition"
    output_path = tmp_path / "exported-application-interface-composition.xml"

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

        import_service.import_from_file("tests/fixtures/xml/application_interface_composition.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="ApplicationComponent"' in xml_text
        assert 'xsi:type="ApplicationInterface"' in xml_text
        assert 'xsi:type="Composition"' in xml_text

        assert 'identifier="app-1"' in xml_text
        assert 'identifier="appi-1"' in xml_text
        assert 'identifier="rel-6"' in xml_text

        assert 'source="app-1"' in xml_text
        assert 'target="appi-1"' in xml_text

        assert "Case App" in xml_text
        assert "Case Interface" in xml_text
        assert "contains" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass