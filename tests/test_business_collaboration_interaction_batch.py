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


def test_parse_model_with_business_collaboration_interaction_batch():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Case Coordination Business Collaboration Model</name>
      <elements>
        <element identifier="buscollab-1" xsi:type="BusinessCollaboration">
          <name xml:lang="en">Case Coordination Team</name>
          <documentation xml:lang="en">Business collaboration coordinating case handling.</documentation>
        </element>
        <element identifier="role-2" xsi:type="BusinessRole">
          <name xml:lang="en">Case Coordinator</name>
          <documentation xml:lang="en">Business role responsible for coordinating case work.</documentation>
        </element>
        <element identifier="actor-2" xsi:type="BusinessActor">
          <name xml:lang="en">Claims Office</name>
          <documentation xml:lang="en">Business actor participating in case coordination.</documentation>
        </element>
        <element identifier="busint-1" xsi:type="BusinessInteraction">
          <name xml:lang="en">Coordinate Case Handling</name>
          <documentation xml:lang="en">Business interaction for coordinated case handling.</documentation>
        </element>
        <element identifier="busevt-1" xsi:type="BusinessEvent">
          <name xml:lang="en">Case Review Requested</name>
          <documentation xml:lang="en">Business event raised when case review is requested.</documentation>
        </element>
        <element identifier="bussvc-2" xsi:type="BusinessService">
          <name xml:lang="en">Case Coordination Service</name>
          <documentation xml:lang="en">Business service for coordinating case handling.</documentation>
        </element>
        <element identifier="busobj-2" xsi:type="BusinessObject">
          <name xml:lang="en">Case File</name>
          <documentation xml:lang="en">Business object containing the case file.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-22"
                      xsi:type="Aggregation"
                      source="buscollab-1"
                      target="role-2">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Business collaboration aggregates business role.</documentation>
        </relationship>
        <relationship identifier="rel-23"
                      xsi:type="Aggregation"
                      source="buscollab-1"
                      target="actor-2">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Business collaboration aggregates business actor.</documentation>
        </relationship>
        <relationship identifier="rel-24"
                      xsi:type="Assignment"
                      source="buscollab-1"
                      target="busint-1">
          <name xml:lang="en">performs</name>
          <documentation xml:lang="en">Business collaboration is assigned to business interaction.</documentation>
        </relationship>
        <relationship identifier="rel-25"
                      xsi:type="Realization"
                      source="busint-1"
                      target="bussvc-2">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Business interaction realizes business service.</documentation>
        </relationship>
        <relationship identifier="rel-26"
                      xsi:type="Access"
                      source="busint-1"
                      target="busobj-2">
          <name xml:lang="en">uses</name>
          <documentation xml:lang="en">Business interaction accesses business object.</documentation>
        </relationship>
        <relationship identifier="rel-27"
                      xsi:type="Triggering"
                      source="busevt-1"
                      target="busint-1">
          <name xml:lang="en">triggers</name>
          <documentation xml:lang="en">Business event triggers business interaction.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 7
    assert len(model.relationships) == 6

    bus_collab = model.get_element("buscollab-1")
    assert bus_collab.xml_type == "BusinessCollaboration"
    assert bus_collab.name == "Case Coordination Team"
    assert (
        bus_collab.documentation
        == "Business collaboration coordinating case handling."
    )

    bus_interaction = model.get_element("busint-1")
    assert bus_interaction.xml_type == "BusinessInteraction"
    assert bus_interaction.name == "Coordinate Case Handling"
    assert (
        bus_interaction.documentation
        == "Business interaction for coordinated case handling."
    )

    bus_event = model.get_element("busevt-1")
    assert bus_event.xml_type == "BusinessEvent"
    assert bus_event.name == "Case Review Requested"
    assert (
        bus_event.documentation
        == "Business event raised when case review is requested."
    )

    rel_aggregation = next(r for r in model.relationships if r.identifier == "rel-22")
    assert rel_aggregation.xml_type == "Aggregation"
    assert rel_aggregation.exchange_type == "Aggregation"
    assert rel_aggregation.source_id == "buscollab-1"
    assert rel_aggregation.target_id == "role-2"
    assert rel_aggregation.name == "contains"
    assert (
        rel_aggregation.documentation
        == "Business collaboration aggregates business role."
    )

    rel_triggering = next(r for r in model.relationships if r.identifier == "rel-27")
    assert rel_triggering.xml_type == "Triggering"
    assert rel_triggering.exchange_type == "Triggering"
    assert rel_triggering.source_id == "busevt-1"
    assert rel_triggering.target_id == "busint-1"
    assert rel_triggering.name == "triggers"
    assert (
        rel_triggering.documentation
        == "Business event triggers business interaction."
    )


def test_build_canonical_import_sparql_with_business_collaboration_interaction_batch():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="buscollab-1",
            xml_type="BusinessCollaboration",
            name="Case Coordination Team",
            documentation="Business collaboration coordinating case handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="role-2",
            xml_type="BusinessRole",
            name="Case Coordinator",
            documentation="Business role responsible for coordinating case work.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="actor-2",
            xml_type="BusinessActor",
            name="Claims Office",
            documentation="Business actor participating in case coordination.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busint-1",
            xml_type="BusinessInteraction",
            name="Coordinate Case Handling",
            documentation="Business interaction for coordinated case handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busevt-1",
            xml_type="BusinessEvent",
            name="Case Review Requested",
            documentation="Business event raised when case review is requested.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="bussvc-2",
            xml_type="BusinessService",
            name="Case Coordination Service",
            documentation="Business service for coordinating case handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busobj-2",
            xml_type="BusinessObject",
            name="Case File",
            documentation="Business object containing the case file.",
        )
    )

    model.add_relationship(
        RelationshipDTO(
            identifier="rel-22",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="buscollab-1",
            target_id="role-2",
            name="contains",
            documentation="Business collaboration aggregates business role.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-23",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="buscollab-1",
            target_id="actor-2",
            name="contains",
            documentation="Business collaboration aggregates business actor.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-24",
            xml_type="Assignment",
            exchange_type="Assignment",
            source_id="buscollab-1",
            target_id="busint-1",
            name="performs",
            documentation="Business collaboration is assigned to business interaction.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-25",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="busint-1",
            target_id="bussvc-2",
            name="realizes",
            documentation="Business interaction realizes business service.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-26",
            xml_type="Access",
            exchange_type="Access",
            source_id="busint-1",
            target_id="busobj-2",
            name="uses",
            documentation="Business interaction accesses business object.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-27",
            xml_type="Triggering",
            exchange_type="Triggering",
            source_id="busevt-1",
            target_id="busint-1",
            name="triggers",
            documentation="Business event triggers business interaction.",
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

    assert "https://purl.org/archimate#BusinessCollaboration" in sparql
    assert "https://purl.org/archimate#BusinessInteraction" in sparql
    assert "https://purl.org/archimate#BusinessEvent" in sparql

    assert 'archimate:identifier "rel-22"' in sparql
    assert 'archimate:identifier "rel-23"' in sparql
    assert 'archimate:identifier "rel-24"' in sparql
    assert 'archimate:identifier "rel-25"' in sparql
    assert 'archimate:identifier "rel-26"' in sparql
    assert 'archimate:identifier "rel-27"' in sparql

    assert (
        "<< ex:buscollab-1 <https://purl.org/archimate#aggregation> ex:role-2 >>"
        in sparql
    )
    assert (
        "<< ex:busevt-1 <https://purl.org/archimate#triggering> ex:busint-1 >>"
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_business_collaboration_interaction_batch_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-business-collaboration-interaction-batch"

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

    buscollab_iri = f"{EX_NS}buscollab-1"
    role2_iri = f"{EX_NS}role-2"
    actor2_iri = f"{EX_NS}actor-2"
    busint_iri = f"{EX_NS}busint-1"
    busevt_iri = f"{EX_NS}busevt-1"
    bussvc2_iri = f"{EX_NS}bussvc-2"
    busobj2_iri = f"{EX_NS}busobj-2"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file(
            "tests/fixtures/xml/business_collaboration_interaction_batch.xml"
        )

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{buscollab_iri}> rdf:type archimate:BusinessCollaboration .
                <{role2_iri}> rdf:type archimate:BusinessRole .
                <{actor2_iri}> rdf:type archimate:BusinessActor .
                <{busint_iri}> rdf:type archimate:BusinessInteraction .
                <{busevt_iri}> rdf:type archimate:BusinessEvent .
                <{bussvc2_iri}> rdf:type archimate:BusinessService .
                <{busobj2_iri}> rdf:type archimate:BusinessObject .

                <{buscollab_iri}> archimate:aggregation <{role2_iri}> .
                <{buscollab_iri}> archimate:aggregation <{actor2_iri}> .
                <{buscollab_iri}> archimate:assignment <{busint_iri}> .
                <{busint_iri}> archimate:realization <{bussvc2_iri}> .
                <{busint_iri}> archimate:access <{busobj2_iri}> .
                <{busevt_iri}> archimate:triggering <{busint_iri}> .

                << <{buscollab_iri}> archimate:aggregation <{role2_iri}> >>
                  archimate:identifier "rel-22" .
                << <{buscollab_iri}> archimate:aggregation <{actor2_iri}> >>
                  archimate:identifier "rel-23" .
                << <{buscollab_iri}> archimate:assignment <{busint_iri}> >>
                  archimate:identifier "rel-24" .
                << <{busint_iri}> archimate:realization <{bussvc2_iri}> >>
                  archimate:identifier "rel-25" .
                << <{busint_iri}> archimate:access <{busobj2_iri}> >>
                  archimate:identifier "rel-26" .
                << <{busevt_iri}> archimate:triggering <{busint_iri}> >>
                  archimate:identifier "rel-27" .
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


def test_export_canonical_rdf_to_xml_includes_business_collaboration_interaction_batch(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-business-collaboration-interaction-batch"
    output_path = tmp_path / "exported-business-collaboration-interaction-batch.xml"

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
            "tests/fixtures/xml/business_collaboration_interaction_batch.xml"
        )
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="BusinessCollaboration"' in xml_text
        assert 'xsi:type="BusinessInteraction"' in xml_text
        assert 'xsi:type="BusinessEvent"' in xml_text
        assert 'xsi:type="Aggregation"' in xml_text
        assert 'xsi:type="Triggering"' in xml_text

        assert 'identifier="buscollab-1"' in xml_text
        assert 'identifier="role-2"' in xml_text
        assert 'identifier="actor-2"' in xml_text
        assert 'identifier="busint-1"' in xml_text
        assert 'identifier="busevt-1"' in xml_text
        assert 'identifier="bussvc-2"' in xml_text
        assert 'identifier="busobj-2"' in xml_text

        assert 'identifier="rel-22"' in xml_text
        assert 'identifier="rel-23"' in xml_text
        assert 'identifier="rel-24"' in xml_text
        assert 'identifier="rel-25"' in xml_text
        assert 'identifier="rel-26"' in xml_text
        assert 'identifier="rel-27"' in xml_text

        assert 'source="buscollab-1"' in xml_text
        assert 'source="busint-1"' in xml_text
        assert 'source="busevt-1"' in xml_text

        assert 'target="role-2"' in xml_text
        assert 'target="actor-2"' in xml_text
        assert 'target="busint-1"' in xml_text
        assert 'target="bussvc-2"' in xml_text
        assert 'target="busobj-2"' in xml_text

        assert "Case Coordination Team" in xml_text
        assert "Coordinate Case Handling" in xml_text
        assert "Case Review Requested" in xml_text
        assert "Case Coordination Service" in xml_text
        assert "Case File" in xml_text
        assert "contains" in xml_text
        assert "Business event triggers business interaction." in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass