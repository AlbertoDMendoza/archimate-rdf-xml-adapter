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


def test_parse_model_with_application_function_and_realization():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Demo model</name>
      <elements>
        <element identifier="appfn-1" xsi:type="ApplicationFunction">
          <name xml:lang="en">Handle Case</name>
          <documentation xml:lang="en">Application function for handling a case.</documentation>
        </element>
        <element identifier="appsvc-1" xsi:type="ApplicationService">
          <name xml:lang="en">Case API</name>
          <documentation xml:lang="en">Application service.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-5"
                      xsi:type="Realization"
                      source="appfn-1"
                      target="appsvc-1">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Application function realizes application service.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 2
    assert len(model.relationships) == 1

    appfn = model.get_element("appfn-1")
    assert appfn.xml_type == "ApplicationFunction"
    assert appfn.name == "Handle Case"
    assert appfn.documentation == "Application function for handling a case."

    appsvc = model.get_element("appsvc-1")
    assert appsvc.xml_type == "ApplicationService"
    assert appsvc.name == "Case API"
    assert appsvc.documentation == "Application service."

    rel = model.relationships[0]
    assert rel.identifier == "rel-5"
    assert rel.xml_type == "Realization"
    assert rel.exchange_type == "Realization"
    assert rel.source_id == "appfn-1"
    assert rel.target_id == "appsvc-1"
    assert rel.name == "realizes"
    assert rel.documentation == "Application function realizes application service."


def test_build_canonical_import_sparql_with_application_function_and_realization():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="appfn-1",
            xml_type="ApplicationFunction",
            name="Handle Case",
            documentation="Application function for handling a case.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appsvc-1",
            xml_type="ApplicationService",
            name="Case API",
            documentation="Application service.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-5",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="appfn-1",
            target_id="appsvc-1",
            name="realizes",
            documentation="Application function realizes application service.",
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

    assert "https://purl.org/archimate#ApplicationFunction" in sparql
    assert "https://purl.org/archimate#ApplicationService" in sparql
    assert "https://purl.org/archimate#realization" in sparql
    assert 'archimate:identifier "rel-5"' in sparql
    assert (
        "<< ex:appfn-1 <https://purl.org/archimate#realization> ex:appsvc-1 >>"
        in sparql
    )
    assert (
        "ex:appfn-1 <https://purl.org/archimate#realization> ex:appsvc-1 ."
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_application_function_and_realization_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-application-function-realization"

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

    appfn_iri = f"{EX_NS}appfn-1"
    appsvc_iri = f"{EX_NS}appsvc-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file("tests/fixtures/xml/application_function_realization.xml")

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{appfn_iri}> rdf:type archimate:ApplicationFunction .
                <{appsvc_iri}> rdf:type archimate:ApplicationService .
                <{appfn_iri}> archimate:realization <{appsvc_iri}> .
                << <{appfn_iri}> archimate:realization <{appsvc_iri}> >>
                  archimate:identifier "rel-5" .
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


def test_export_canonical_rdf_to_xml_includes_application_function_and_realization(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-application-function-realization"
    output_path = tmp_path / "exported-application-function-realization.xml"

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

        import_service.import_from_file("tests/fixtures/xml/application_function_realization.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="ApplicationFunction"' in xml_text
        assert 'xsi:type="ApplicationService"' in xml_text
        assert 'xsi:type="Realization"' in xml_text

        assert 'identifier="appfn-1"' in xml_text
        assert 'identifier="appsvc-1"' in xml_text
        assert 'identifier="rel-5"' in xml_text

        assert 'source="appfn-1"' in xml_text
        assert 'target="appsvc-1"' in xml_text

        assert "Handle Case" in xml_text
        assert "Case API" in xml_text
        assert "realizes" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass