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


def test_parse_model_with_business_completion_batch():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Business Completion Batch Model</name>
      <elements>
        <element identifier="role-3" xsi:type="BusinessRole">
          <name xml:lang="en">Case Service Coordinator</name>
          <documentation xml:lang="en">Business role coordinating case services.</documentation>
        </element>
        <element identifier="role-4" xsi:type="BusinessRole">
          <name xml:lang="en">Service Staff</name>
          <documentation xml:lang="en">General business role for service staff.</documentation>
        </element>
        <element identifier="busif-1" xsi:type="BusinessInterface">
          <name xml:lang="en">Case Service Desk</name>
          <documentation xml:lang="en">Business interface exposing case support.</documentation>
        </element>
        <element identifier="bussvc-3" xsi:type="BusinessService">
          <name xml:lang="en">Case Support Service</name>
          <documentation xml:lang="en">Business service for case support.</documentation>
        </element>
        <element identifier="contract-1" xsi:type="Contract">
          <name xml:lang="en">Case Support Agreement</name>
          <documentation xml:lang="en">Business contract governing case support.</documentation>
        </element>
        <element identifier="product-1" xsi:type="Product">
          <name xml:lang="en">Case Support Offering</name>
          <documentation xml:lang="en">Product offering for coordinated case support.</documentation>
        </element>
        <element identifier="representation-1" xsi:type="Representation">
          <name xml:lang="en">Case Summary Document</name>
          <documentation xml:lang="en">Representation of case information for staff.</documentation>
        </element>
        <element identifier="busobj-3" xsi:type="BusinessObject">
          <name xml:lang="en">Case File</name>
          <documentation xml:lang="en">Business object containing the case file.</documentation>
        </element>
        <element identifier="busproc-2" xsi:type="BusinessProcess">
          <name xml:lang="en">Review Case</name>
          <documentation xml:lang="en">Business process for reviewing a case.</documentation>
        </element>
        <element identifier="busproc-3" xsi:type="BusinessProcess">
          <name xml:lang="en">Resolve Case</name>
          <documentation xml:lang="en">Business process for resolving a case.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-28"
                      xsi:type="Composition"
                      source="role-3"
                      target="busif-1">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Business role is composed of business interface.</documentation>
        </relationship>
        <relationship identifier="rel-29"
                      xsi:type="Assignment"
                      source="busif-1"
                      target="bussvc-3">
          <name xml:lang="en">assigns</name>
          <documentation xml:lang="en">Business interface assigns business service.</documentation>
        </relationship>
        <relationship identifier="rel-30"
                      xsi:type="Association"
                      source="bussvc-3"
                      target="contract-1">
          <name xml:lang="en">is governed by</name>
          <documentation xml:lang="en">Business service is associated with business contract.</documentation>
        </relationship>
        <relationship identifier="rel-31"
                      xsi:type="Aggregation"
                      source="product-1"
                      target="bussvc-3">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Product aggregates business service.</documentation>
        </relationship>
        <relationship identifier="rel-32"
                      xsi:type="Aggregation"
                      source="product-1"
                      target="contract-1">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Product aggregates business contract.</documentation>
        </relationship>
        <relationship identifier="rel-33"
                      xsi:type="Realization"
                      source="representation-1"
                      target="busobj-3">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Representation realizes business object.</documentation>
        </relationship>
        <relationship identifier="rel-34"
                      xsi:type="Access"
                      source="busproc-2"
                      target="representation-1">
          <name xml:lang="en">uses</name>
          <documentation xml:lang="en">Business process accesses representation.</documentation>
        </relationship>
        <relationship identifier="rel-35"
                      xsi:type="Flow"
                      source="busproc-2"
                      target="busproc-3">
          <name xml:lang="en">flows to</name>
          <documentation xml:lang="en">Business process flows into following business process.</documentation>
        </relationship>
        <relationship identifier="rel-36"
                      xsi:type="Influence"
                      source="busproc-2"
                      target="busproc-3">
          <name xml:lang="en">influences</name>
          <documentation xml:lang="en">Business process influences following business process.</documentation>
        </relationship>
        <relationship identifier="rel-37"
                      xsi:type="Specialization"
                      source="role-3"
                      target="role-4">
          <name xml:lang="en">specializes</name>
          <documentation xml:lang="en">Business role specializes more general business role.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 10
    assert len(model.relationships) == 10

    business_interface = model.get_element("busif-1")
    assert business_interface.xml_type == "BusinessInterface"
    assert business_interface.name == "Case Service Desk"

    business_contract = model.get_element("contract-1")
    assert business_contract.xml_type == "Contract"
    assert business_contract.name == "Case Support Agreement"

    representation = model.get_element("representation-1")
    assert representation.xml_type == "Representation"
    assert representation.name == "Case Summary Document"

    product = model.get_element("product-1")
    assert product.xml_type == "Product"
    assert product.name == "Case Support Offering"

    rel_association = next(r for r in model.relationships if r.identifier == "rel-30")
    assert rel_association.xml_type == "Association"
    assert rel_association.source_id == "bussvc-3"
    assert rel_association.target_id == "contract-1"

    rel_flow = next(r for r in model.relationships if r.identifier == "rel-35")
    assert rel_flow.xml_type == "Flow"
    assert rel_flow.source_id == "busproc-2"
    assert rel_flow.target_id == "busproc-3"

    rel_influence = next(r for r in model.relationships if r.identifier == "rel-36")
    assert rel_influence.xml_type == "Influence"
    assert rel_influence.source_id == "busproc-2"
    assert rel_influence.target_id == "busproc-3"

    rel_specialization = next(
        r for r in model.relationships if r.identifier == "rel-37"
    )
    assert rel_specialization.xml_type == "Specialization"
    assert rel_specialization.source_id == "role-3"
    assert rel_specialization.target_id == "role-4"


def test_build_canonical_import_sparql_with_business_completion_batch():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="role-3",
            xml_type="BusinessRole",
            name="Case Service Coordinator",
            documentation="Business role coordinating case services.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="role-4",
            xml_type="BusinessRole",
            name="Service Staff",
            documentation="General business role for service staff.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busif-1",
            xml_type="BusinessInterface",
            name="Case Service Desk",
            documentation="Business interface exposing case support.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="bussvc-3",
            xml_type="BusinessService",
            name="Case Support Service",
            documentation="Business service for case support.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="contract-1",
            xml_type="Contract",
            name="Case Support Agreement",
            documentation="Business contract governing case support.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="product-1",
            xml_type="Product",
            name="Case Support Offering",
            documentation="Product offering for coordinated case support.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="representation-1",
            xml_type="Representation",
            name="Case Summary Document",
            documentation="Representation of case information for staff.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busobj-3",
            xml_type="BusinessObject",
            name="Case File",
            documentation="Business object containing the case file.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busproc-2",
            xml_type="BusinessProcess",
            name="Review Case",
            documentation="Business process for reviewing a case.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busproc-3",
            xml_type="BusinessProcess",
            name="Resolve Case",
            documentation="Business process for resolving a case.",
        )
    )

    relationships = [
        RelationshipDTO(
            identifier="rel-28",
            xml_type="Composition",
            exchange_type="Composition",
            source_id="role-3",
            target_id="busif-1",
            name="contains",
            documentation="Business role is composed of business interface.",
        ),
        RelationshipDTO(
            identifier="rel-29",
            xml_type="Serving",
            exchange_type="Serving",
            source_id="busif-1",
            target_id="bussvc-3",
            name="serves",
            documentation="Business interface serves business service.",
        ),
        RelationshipDTO(
            identifier="rel-30",
            xml_type="Association",
            exchange_type="Association",
            source_id="bussvc-3",
            target_id="contract-1",
            name="is governed by",
            documentation="Business service is associated with business contract.",
        ),
        RelationshipDTO(
            identifier="rel-31",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="product-1",
            target_id="bussvc-3",
            name="contains",
            documentation="Product aggregates business service.",
        ),
        RelationshipDTO(
            identifier="rel-32",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="product-1",
            target_id="contract-1",
            name="contains",
            documentation="Product aggregates business contract.",
        ),
        RelationshipDTO(
            identifier="rel-33",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="representation-1",
            target_id="busobj-3",
            name="realizes",
            documentation="Representation realizes business object.",
        ),
        RelationshipDTO(
            identifier="rel-34",
            xml_type="Access",
            exchange_type="Access",
            source_id="busproc-2",
            target_id="representation-1",
            name="uses",
            documentation="Business process accesses representation.",
        ),
        RelationshipDTO(
            identifier="rel-35",
            xml_type="Flow",
            exchange_type="Flow",
            source_id="busproc-2",
            target_id="busproc-3",
            name="flows to",
            documentation="Business process flows into following business process.",
        ),
        RelationshipDTO(
            identifier="rel-36",
            xml_type="Influence",
            exchange_type="Influence",
            source_id="busproc-2",
            target_id="busproc-3",
            name="influences",
            documentation="Business process influences following business process.",
        ),
        RelationshipDTO(
            identifier="rel-37",
            xml_type="Specialization",
            exchange_type="Specialization",
            source_id="role-3",
            target_id="role-4",
            name="specializes",
            documentation="Business role specializes more general business role.",
        ),
    ]

    for relationship in relationships:
        model.add_relationship(relationship)

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

    assert "https://purl.org/archimate#BusinessInterface" in sparql
    assert "https://purl.org/archimate#Contract" in sparql
    assert "https://purl.org/archimate#Representation" in sparql
    assert "https://purl.org/archimate#Product" in sparql

    assert "https://purl.org/archimate#association" in sparql
    assert "https://purl.org/archimate#flow" in sparql
    assert "https://purl.org/archimate#influence" in sparql
    assert "https://purl.org/archimate#specialization" in sparql

    for rel_id in range(28, 38):
        assert f'archimate:identifier "rel-{rel_id}"' in sparql

    assert (
        "<< ex:bussvc-3 <https://purl.org/archimate#association> ex:contract-1 >>"
        in sparql
    )
    assert (
        "<< ex:busproc-2 <https://purl.org/archimate#flow> ex:busproc-3 >>"
        in sparql
    )
    assert (
        "<< ex:busproc-2 <https://purl.org/archimate#influence> ex:busproc-3 >>"
        in sparql
    )
    assert (
        "<< ex:role-3 <https://purl.org/archimate#specialization> ex:role-4 >>"
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_business_completion_batch_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-business-completion-batch"

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

    role3_iri = f"{EX_NS}role-3"
    role4_iri = f"{EX_NS}role-4"
    busif_iri = f"{EX_NS}busif-1"
    bussvc3_iri = f"{EX_NS}bussvc-3"
    contract1_iri = f"{EX_NS}contract-1"
    product1_iri = f"{EX_NS}product-1"
    representation1_iri = f"{EX_NS}representation-1"
    busobj3_iri = f"{EX_NS}busobj-3"
    busproc2_iri = f"{EX_NS}busproc-2"
    busproc3_iri = f"{EX_NS}busproc-3"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file("tests/fixtures/xml/business_completion_batch.xml")

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{role3_iri}> rdf:type archimate:BusinessRole .
                <{role4_iri}> rdf:type archimate:BusinessRole .
                <{busif_iri}> rdf:type archimate:BusinessInterface .
                <{bussvc3_iri}> rdf:type archimate:BusinessService .
                <{contract1_iri}> rdf:type archimate:Contract .
                <{product1_iri}> rdf:type archimate:Product .
                <{representation1_iri}> rdf:type archimate:Representation .
                <{busobj3_iri}> rdf:type archimate:BusinessObject .
                <{busproc2_iri}> rdf:type archimate:BusinessProcess .
                <{busproc3_iri}> rdf:type archimate:BusinessProcess .

                <{role3_iri}> archimate:composition <{busif_iri}> .
                <{busif_iri}> archimate:assignment <{bussvc3_iri}> .
                <{bussvc3_iri}> archimate:association <{contract1_iri}> .
                <{product1_iri}> archimate:aggregation <{bussvc3_iri}> .
                <{product1_iri}> archimate:aggregation <{contract1_iri}> .
                <{representation1_iri}> archimate:realization <{busobj3_iri}> .
                <{busproc2_iri}> archimate:access <{representation1_iri}> .
                <{busproc2_iri}> archimate:flow <{busproc3_iri}> .
                <{busproc2_iri}> archimate:influence <{busproc3_iri}> .
                <{role3_iri}> archimate:specialization <{role4_iri}> .

                << <{role3_iri}> archimate:composition <{busif_iri}> >>
                  archimate:identifier "rel-28" .
                << <{busif_iri}> archimate:assignment <{bussvc3_iri}> >>
                  archimate:identifier "rel-29" .
                << <{bussvc3_iri}> archimate:association <{contract1_iri}> >>
                  archimate:identifier "rel-30" .
                << <{product1_iri}> archimate:aggregation <{bussvc3_iri}> >>
                  archimate:identifier "rel-31" .
                << <{product1_iri}> archimate:aggregation <{contract1_iri}> >>
                  archimate:identifier "rel-32" .
                << <{representation1_iri}> archimate:realization <{busobj3_iri}> >>
                  archimate:identifier "rel-33" .
                << <{busproc2_iri}> archimate:access <{representation1_iri}> >>
                  archimate:identifier "rel-34" .
                << <{busproc2_iri}> archimate:flow <{busproc3_iri}> >>
                  archimate:identifier "rel-35" .
                << <{busproc2_iri}> archimate:influence <{busproc3_iri}> >>
                  archimate:identifier "rel-36" .
                << <{role3_iri}> archimate:specialization <{role4_iri}> >>
                  archimate:identifier "rel-37" .
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


def test_export_canonical_rdf_to_xml_includes_business_completion_batch(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-business-completion-batch"
    output_path = tmp_path / "exported-business-completion-batch.xml"

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

        import_service.import_from_file("tests/fixtures/xml/business_completion_batch.xml")
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="BusinessInterface"' in xml_text
        assert 'xsi:type="Contract"' in xml_text
        assert 'xsi:type="Representation"' in xml_text
        assert 'xsi:type="Product"' in xml_text

        assert 'xsi:type="Association"' in xml_text
        assert 'xsi:type="Flow"' in xml_text
        assert 'xsi:type="Influence"' in xml_text
        assert 'xsi:type="Specialization"' in xml_text

        for identifier in [
            "role-3",
            "role-4",
            "busif-1",
            "bussvc-3",
            "contract-1",
            "product-1",
            "representation-1",
            "busobj-3",
            "busproc-2",
            "busproc-3",
        ]:
            assert f'identifier="{identifier}"' in xml_text

        for rel_id in range(28, 38):
            assert f'identifier="rel-{rel_id}"' in xml_text

        assert 'source="role-3"' in xml_text
        assert 'source="busif-1"' in xml_text
        assert 'source="bussvc-3"' in xml_text
        assert 'source="product-1"' in xml_text
        assert 'source="representation-1"' in xml_text
        assert 'source="busproc-2"' in xml_text

        assert 'target="busif-1"' in xml_text
        assert 'target="bussvc-3"' in xml_text
        assert 'target="contract-1"' in xml_text
        assert 'target="busobj-3"' in xml_text
        assert 'target="representation-1"' in xml_text
        assert 'target="busproc-3"' in xml_text
        assert 'target="role-4"' in xml_text

        assert "Case Service Desk" in xml_text
        assert "Case Support Agreement" in xml_text
        assert "Case Support Offering" in xml_text
        assert "Case Summary Document" in xml_text
        assert "is governed by" in xml_text
        assert "flows to" in xml_text
        assert "influences" in xml_text
        assert "specializes" in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass
