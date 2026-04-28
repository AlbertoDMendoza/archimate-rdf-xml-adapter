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


def test_parse_model_with_business_function_service_and_role_assignment():
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
        <element identifier="busfn-1" xsi:type="BusinessFunction">
          <name xml:lang="en">Handle Requests</name>
          <documentation xml:lang="en">Business function for handling requests.</documentation>
        </element>
        <element identifier="bussvc-1" xsi:type="BusinessService">
          <name xml:lang="en">Request Handling Service</name>
          <documentation xml:lang="en">Business service for request handling.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-8"
                      xsi:type="Realization"
                      source="busfn-1"
                      target="bussvc-1">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Business function realizes business service.</documentation>
        </relationship>
        <relationship identifier="rel-9"
                      xsi:type="Assignment"
                      source="role-1"
                      target="busfn-1">
          <name xml:lang="en">is responsible for</name>
          <documentation xml:lang="en">Business role is assigned to business function.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 3
    assert len(model.relationships) == 2

    role = model.get_element("role-1")
    assert role.xml_type == "BusinessRole"
    assert role.name == "Case Handler"
    assert role.documentation == "Business role for handling cases."

    busfn = model.get_element("busfn-1")
    assert busfn.xml_type == "BusinessFunction"
    assert busfn.name == "Handle Requests"
    assert busfn.documentation == "Business function for handling requests."

    bussvc = model.get_element("bussvc-1")
    assert bussvc.xml_type == "BusinessService"
    assert bussvc.name == "Request Handling Service"
    assert bussvc.documentation == "Business service for request handling."

    rel_realization = next(r for r in model.relationships if r.identifier == "rel-8")
    assert rel_realization.xml_type == "Realization"
    assert rel_realization.exchange_type == "Realization"
    assert rel_realization.source_id == "busfn-1"
    assert rel_realization.target_id == "bussvc-1"
    assert rel_realization.name == "realizes"
    assert (
        rel_realization.documentation
        == "Business function realizes business service."
    )

    rel_assignment = next(r for r in model.relationships if r.identifier == "rel-9")
    assert rel_assignment.xml_type == "Assignment"
    assert rel_assignment.exchange_type == "Assignment"
    assert rel_assignment.source_id == "role-1"
    assert rel_assignment.target_id == "busfn-1"
    assert rel_assignment.name == "is responsible for"
    assert (
        rel_assignment.documentation
        == "Business role is assigned to business function."
    )


def test_build_canonical_import_sparql_with_business_function_service_and_role_assignment():
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
            identifier="busfn-1",
            xml_type="BusinessFunction",
            name="Handle Requests",
            documentation="Business function for handling requests.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="bussvc-1",
            xml_type="BusinessService",
            name="Request Handling Service",
            documentation="Business service for request handling.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-8",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="busfn-1",
            target_id="bussvc-1",
            name="realizes",
            documentation="Business function realizes business service.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-9",
            xml_type="Assignment",
            exchange_type="Assignment",
            source_id="role-1",
            target_id="busfn-1",
            name="is responsible for",
            documentation="Business role is assigned to business function.",
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
    assert "https://purl.org/archimate#BusinessFunction" in sparql
    assert "https://purl.org/archimate#BusinessService" in sparql
    assert "https://purl.org/archimate#realization" in sparql
    assert "https://purl.org/archimate#assignment" in sparql

    assert 'archimate:identifier "rel-8"' in sparql
    assert 'archimate:identifier "rel-9"' in sparql

    assert (
        "<< ex:busfn-1 <https://purl.org/archimate#realization> ex:bussvc-1 >>"
        in sparql
    )
    assert (
        "<< ex:role-1 <https://purl.org/archimate#assignment> ex:busfn-1 >>"
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_business_function_service_and_role_assignment_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-business-function-service-role-assignment"

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

    role_iri = f"{EX_NS}role-1"
    busfn_iri = f"{EX_NS}busfn-1"
    bussvc_iri = f"{EX_NS}bussvc-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file(
            "tests/fixtures/xml/business_function_service_and_role_assignment.xml"
        )

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{role_iri}> rdf:type archimate:BusinessRole .
                <{busfn_iri}> rdf:type archimate:BusinessFunction .
                <{bussvc_iri}> rdf:type archimate:BusinessService .

                <{busfn_iri}> archimate:realization <{bussvc_iri}> .
                <{role_iri}> archimate:assignment <{busfn_iri}> .

                << <{busfn_iri}> archimate:realization <{bussvc_iri}> >>
                  archimate:identifier "rel-8" .
                << <{role_iri}> archimate:assignment <{busfn_iri}> >>
                  archimate:identifier "rel-9" .
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


def test_export_canonical_rdf_to_xml_includes_business_function_service_and_role_assignment(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-business-function-service-role-assignment"
    output_path = tmp_path / "exported-business-function-service-role-assignment.xml"

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

        import_service.import_from_file(
            "tests/fixtures/xml/business_function_service_and_role_assignment.xml"
        )
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="BusinessRole"' in xml_text
        assert 'xsi:type="BusinessFunction"' in xml_text
        assert 'xsi:type="BusinessService"' in xml_text
        assert 'xsi:type="Assignment"' in xml_text
        assert 'xsi:type="Realization"' in xml_text

        assert 'identifier="role-1"' in xml_text
        assert 'identifier="busfn-1"' in xml_text
        assert 'identifier="bussvc-1"' in xml_text
        assert 'identifier="rel-8"' in xml_text
        assert 'identifier="rel-9"' in xml_text

        assert 'source="busfn-1"' in xml_text
        assert 'target="bussvc-1"' in xml_text
        assert 'source="role-1"' in xml_text
        assert 'target="busfn-1"' in xml_text

        assert "Case Handler" in xml_text
        assert "Handle Requests" in xml_text
        assert "Request Handling Service" in xml_text
        assert "realizes" in xml_text
        assert "is responsible for" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass