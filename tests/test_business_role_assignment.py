from pathlib import Path

import pytest

from archimate_adapter.dto.model import ElementDTO, ModelDTO, RelationshipDTO
from archimate_adapter.config import GRAPHDB_BASE_URL
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


def test_parse_model_with_business_role_and_assignment():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Demo model</name>
      <elements>
        <element identifier="role-1" xsi:type="BusinessRole">
          <name xml:lang="en">Case Handler</name>
          <documentation xml:lang="en">Business role for handling cases.</documentation>
        </element>
        <element identifier="process-1" xsi:type="BusinessProcess">
          <name xml:lang="en">Handle Application</name>
          <documentation xml:lang="en">Business process for handling an application.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-7"
                      xsi:type="Assignment"
                      source="role-1"
                      target="process-1">
          <name xml:lang="en">is responsible for</name>
          <documentation xml:lang="en">Business role is assigned to business process.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 2
    assert len(model.relationships) == 1

    role = model.get_element("role-1")
    assert role.xml_type == "BusinessRole"
    assert role.name == "Case Handler"
    assert role.documentation == "Business role for handling cases."

    process = model.get_element("process-1")
    assert process.xml_type == "BusinessProcess"
    assert process.name == "Handle Application"
    assert process.documentation == "Business process for handling an application."

    rel = model.relationships[0]
    assert rel.identifier == "rel-7"
    assert rel.xml_type == "Assignment"
    assert rel.exchange_type == "Assignment"
    assert rel.source_id == "role-1"
    assert rel.target_id == "process-1"
    assert rel.name == "is responsible for"
    assert rel.documentation == "Business role is assigned to business process."


def test_build_canonical_import_sparql_with_business_role_and_assignment():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="role-1",
            xml_type="BusinessRole",
            name="Case Handler",
            documentation="Business role for handling cases.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="process-1",
            xml_type="BusinessProcess",
            name="Handle Application",
            documentation="Business process for handling an application.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-7",
            xml_type="Assignment",
            exchange_type="Assignment",
            source_id="role-1",
            target_id="process-1",
            name="is responsible for",
            documentation="Business role is assigned to business process.",
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

    assert "https://purl.org/archimate#BusinessRole" in sparql
    assert "https://purl.org/archimate#BusinessProcess" in sparql
    assert "https://purl.org/archimate#assignment" in sparql
    assert 'archimate:identifier "rel-7"' in sparql
    assert (
        "<< ex:role-1 <https://purl.org/archimate#assignment> ex:process-1 >>"
        in sparql
    )
    assert (
        "ex:role-1 <https://purl.org/archimate#assignment> ex:process-1 ."
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_business_role_and_assignment_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-business-role-assignment"

    client = GraphDBClient(
        base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
    )

    service = ImportXmlToCanonicalRdfService(
        graphdb_base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=graph_iri,
    )

    role_iri = f"{EX_NS}role-1"
    process_iri = f"{EX_NS}process-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file("tests/fixtures/xml/business_role_assignment.xml")

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{role_iri}> rdf:type archimate:BusinessRole .
                <{process_iri}> rdf:type archimate:BusinessProcess .
                <{role_iri}> archimate:assignment <{process_iri}> .
                << <{role_iri}> archimate:assignment <{process_iri}> >>
                  archimate:identifier "rel-7" .
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


def test_export_canonical_rdf_to_xml_includes_business_role_and_assignment(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-business-role-assignment"
    output_path = tmp_path / "exported-business-role-assignment.xml"

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

        import_service.import_from_file("tests/fixtures/xml/business_role_assignment.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="BusinessRole"' in xml_text
        assert 'xsi:type="BusinessProcess"' in xml_text
        assert 'xsi:type="Assignment"' in xml_text

        assert 'identifier="role-1"' in xml_text
        assert 'identifier="process-1"' in xml_text
        assert 'identifier="rel-7"' in xml_text

        assert 'source="role-1"' in xml_text
        assert 'target="process-1"' in xml_text

        assert "Case Handler" in xml_text
        assert "Handle Application" in xml_text
        assert "is responsible for" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass
