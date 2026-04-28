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


def test_parse_model_with_application_collaboration_interaction_batch():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Multi-System Claim Coordination Model</name>
      <elements>
        <element identifier="appcomp-2" xsi:type="ApplicationComponent">
          <name xml:lang="en">Claims Intake Application</name>
          <documentation xml:lang="en">Application component for receiving incoming claims.</documentation>
        </element>
        <element identifier="appcomp-3" xsi:type="ApplicationComponent">
          <name xml:lang="en">Claims Validation Application</name>
          <documentation xml:lang="en">Application component for validating claim details.</documentation>
        </element>
        <element identifier="appcollab-1" xsi:type="ApplicationCollaboration">
          <name xml:lang="en">Claims Coordination Collaboration</name>
          <documentation xml:lang="en">Application collaboration of components coordinating claim handling.</documentation>
        </element>
        <element identifier="appint-1" xsi:type="ApplicationInteraction">
          <name xml:lang="en">Coordinate Claim Handling</name>
          <documentation xml:lang="en">Application interaction for coordinated claim handling.</documentation>
        </element>
        <element identifier="appevt-2" xsi:type="ApplicationEvent">
          <name xml:lang="en">Claim Validation Requested</name>
          <documentation xml:lang="en">Application event raised when claim validation is requested.</documentation>
        </element>
        <element identifier="appsvc-2" xsi:type="ApplicationService">
          <name xml:lang="en">Claim Coordination Service</name>
          <documentation xml:lang="en">Application service for coordinating claim handling.</documentation>
        </element>
        <element identifier="dataobj-2" xsi:type="DataObject">
          <name xml:lang="en">Validation Record</name>
          <documentation xml:lang="en">Data object containing validation information.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-16"
                      xsi:type="Aggregation"
                      source="appcollab-1"
                      target="appcomp-2">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Application collaboration aggregates application component.</documentation>
        </relationship>
        <relationship identifier="rel-17"
                      xsi:type="Aggregation"
                      source="appcollab-1"
                      target="appcomp-3">
          <name xml:lang="en">contains</name>
          <documentation xml:lang="en">Application collaboration aggregates application component.</documentation>
        </relationship>
        <relationship identifier="rel-18"
                      xsi:type="Assignment"
                      source="appcollab-1"
                      target="appint-1">
          <name xml:lang="en">performs</name>
          <documentation xml:lang="en">Application collaboration is assigned to application interaction.</documentation>
        </relationship>
        <relationship identifier="rel-19"
                      xsi:type="Realization"
                      source="appint-1"
                      target="appsvc-2">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Application interaction realizes application service.</documentation>
        </relationship>
        <relationship identifier="rel-20"
                      xsi:type="Access"
                      source="appint-1"
                      target="dataobj-2">
          <name xml:lang="en">uses</name>
          <documentation xml:lang="en">Application interaction accesses validation data.</documentation>
        </relationship>
        <relationship identifier="rel-21"
                      xsi:type="Triggering"
                      source="appevt-2"
                      target="appint-1">
          <name xml:lang="en">triggers</name>
          <documentation xml:lang="en">Application event triggers application interaction.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 7
    assert len(model.relationships) == 6

    app_collab = model.get_element("appcollab-1")
    assert app_collab.xml_type == "ApplicationCollaboration"
    assert app_collab.name == "Claims Coordination Collaboration"
    assert (
        app_collab.documentation
        == "Application collaboration of components coordinating claim handling."
    )

    app_interaction = model.get_element("appint-1")
    assert app_interaction.xml_type == "ApplicationInteraction"
    assert app_interaction.name == "Coordinate Claim Handling"
    assert (
        app_interaction.documentation
        == "Application interaction for coordinated claim handling."
    )

    rel_aggregation = next(r for r in model.relationships if r.identifier == "rel-16")
    assert rel_aggregation.xml_type == "Aggregation"
    assert rel_aggregation.exchange_type == "Aggregation"
    assert rel_aggregation.source_id == "appcollab-1"
    assert rel_aggregation.target_id == "appcomp-2"
    assert rel_aggregation.name == "contains"
    assert (
        rel_aggregation.documentation
        == "Application collaboration aggregates application component."
    )

    rel_triggering = next(r for r in model.relationships if r.identifier == "rel-21")
    assert rel_triggering.xml_type == "Triggering"
    assert rel_triggering.exchange_type == "Triggering"
    assert rel_triggering.source_id == "appevt-2"
    assert rel_triggering.target_id == "appint-1"
    assert rel_triggering.name == "triggers"
    assert (
        rel_triggering.documentation
        == "Application event triggers application interaction."
    )


def test_build_canonical_import_sparql_with_application_collaboration_interaction_batch():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="appcomp-2",
            xml_type="ApplicationComponent",
            name="Claims Intake Application",
            documentation="Application component for receiving incoming claims.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appcomp-3",
            xml_type="ApplicationComponent",
            name="Claims Validation Application",
            documentation="Application component for validating claim details.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appcollab-1",
            xml_type="ApplicationCollaboration",
            name="Claims Coordination Collaboration",
            documentation="Application collaboration of components coordinating claim handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appint-1",
            xml_type="ApplicationInteraction",
            name="Coordinate Claim Handling",
            documentation="Application interaction for coordinated claim handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appevt-2",
            xml_type="ApplicationEvent",
            name="Claim Validation Requested",
            documentation="Application event raised when claim validation is requested.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appsvc-2",
            xml_type="ApplicationService",
            name="Claim Coordination Service",
            documentation="Application service for coordinating claim handling.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="dataobj-2",
            xml_type="DataObject",
            name="Validation Record",
            documentation="Data object containing validation information.",
        )
    )

    model.add_relationship(
        RelationshipDTO(
            identifier="rel-16",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="appcollab-1",
            target_id="appcomp-2",
            name="contains",
            documentation="Application collaboration aggregates application component.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-17",
            xml_type="Aggregation",
            exchange_type="Aggregation",
            source_id="appcollab-1",
            target_id="appcomp-3",
            name="contains",
            documentation="Application collaboration aggregates application component.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-18",
            xml_type="Assignment",
            exchange_type="Assignment",
            source_id="appcollab-1",
            target_id="appint-1",
            name="performs",
            documentation="Application collaboration is assigned to application interaction.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-19",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="appint-1",
            target_id="appsvc-2",
            name="realizes",
            documentation="Application interaction realizes application service.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-20",
            xml_type="Access",
            exchange_type="Access",
            source_id="appint-1",
            target_id="dataobj-2",
            name="uses",
            documentation="Application interaction accesses validation data.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-21",
            xml_type="Triggering",
            exchange_type="Triggering",
            source_id="appevt-2",
            target_id="appint-1",
            name="triggers",
            documentation="Application event triggers application interaction.",
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

    assert "https://purl.org/archimate#ApplicationCollaboration" in sparql
    assert "https://purl.org/archimate#ApplicationInteraction" in sparql
    assert "https://purl.org/archimate#aggregation" in sparql

    assert 'archimate:identifier "rel-16"' in sparql
    assert 'archimate:identifier "rel-17"' in sparql
    assert 'archimate:identifier "rel-18"' in sparql
    assert 'archimate:identifier "rel-19"' in sparql
    assert 'archimate:identifier "rel-20"' in sparql
    assert 'archimate:identifier "rel-21"' in sparql

    assert (
        "<< ex:appcollab-1 <https://purl.org/archimate#aggregation> ex:appcomp-2 >>"
        in sparql
    )
    assert (
        "<< ex:appevt-2 <https://purl.org/archimate#triggering> ex:appint-1 >>"
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_application_collaboration_interaction_batch_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-application-collaboration-interaction-batch"

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

    appcomp2_iri = f"{EX_NS}appcomp-2"
    appcomp3_iri = f"{EX_NS}appcomp-3"
    appcollab_iri = f"{EX_NS}appcollab-1"
    appint_iri = f"{EX_NS}appint-1"
    appevt2_iri = f"{EX_NS}appevt-2"
    appsvc2_iri = f"{EX_NS}appsvc-2"
    dataobj2_iri = f"{EX_NS}dataobj-2"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file(
            "tests/fixtures/xml/application_collaboration_interaction_batch.xml"
        )

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{appcomp2_iri}> rdf:type archimate:ApplicationComponent .
                <{appcomp3_iri}> rdf:type archimate:ApplicationComponent .
                <{appcollab_iri}> rdf:type archimate:ApplicationCollaboration .
                <{appint_iri}> rdf:type archimate:ApplicationInteraction .
                <{appevt2_iri}> rdf:type archimate:ApplicationEvent .
                <{appsvc2_iri}> rdf:type archimate:ApplicationService .
                <{dataobj2_iri}> rdf:type archimate:DataObject .

                <{appcollab_iri}> archimate:aggregation <{appcomp2_iri}> .
                <{appcollab_iri}> archimate:aggregation <{appcomp3_iri}> .
                <{appcollab_iri}> archimate:assignment <{appint_iri}> .
                <{appint_iri}> archimate:realization <{appsvc2_iri}> .
                <{appint_iri}> archimate:access <{dataobj2_iri}> .
                <{appevt2_iri}> archimate:triggering <{appint_iri}> .

                << <{appcollab_iri}> archimate:aggregation <{appcomp2_iri}> >>
                  archimate:identifier "rel-16" .
                << <{appcollab_iri}> archimate:aggregation <{appcomp3_iri}> >>
                  archimate:identifier "rel-17" .
                << <{appcollab_iri}> archimate:assignment <{appint_iri}> >>
                  archimate:identifier "rel-18" .
                << <{appint_iri}> archimate:realization <{appsvc2_iri}> >>
                  archimate:identifier "rel-19" .
                << <{appint_iri}> archimate:access <{dataobj2_iri}> >>
                  archimate:identifier "rel-20" .
                << <{appevt2_iri}> archimate:triggering <{appint_iri}> >>
                  archimate:identifier "rel-21" .
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


def test_export_canonical_rdf_to_xml_includes_application_collaboration_interaction_batch(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-application-collaboration-interaction-batch"
    output_path = (
        tmp_path / "exported-application-collaboration-interaction-batch.xml"
    )

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
            "tests/fixtures/xml/application_collaboration_interaction_batch.xml"
        )
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="ApplicationCollaboration"' in xml_text
        assert 'xsi:type="ApplicationInteraction"' in xml_text
        assert 'xsi:type="Aggregation"' in xml_text
        assert 'xsi:type="Triggering"' in xml_text

        assert 'identifier="appcomp-2"' in xml_text
        assert 'identifier="appcomp-3"' in xml_text
        assert 'identifier="appcollab-1"' in xml_text
        assert 'identifier="appint-1"' in xml_text
        assert 'identifier="appevt-2"' in xml_text
        assert 'identifier="appsvc-2"' in xml_text
        assert 'identifier="dataobj-2"' in xml_text

        assert 'identifier="rel-16"' in xml_text
        assert 'identifier="rel-17"' in xml_text
        assert 'identifier="rel-18"' in xml_text
        assert 'identifier="rel-19"' in xml_text
        assert 'identifier="rel-20"' in xml_text
        assert 'identifier="rel-21"' in xml_text

        assert 'source="appcollab-1"' in xml_text
        assert 'source="appint-1"' in xml_text
        assert 'source="appevt-2"' in xml_text

        assert 'target="appcomp-2"' in xml_text
        assert 'target="appcomp-3"' in xml_text
        assert 'target="appint-1"' in xml_text
        assert 'target="appsvc-2"' in xml_text
        assert 'target="dataobj-2"' in xml_text

        assert "Claims Coordination Collaboration" in xml_text
        assert "Coordinate Claim Handling" in xml_text
        assert "Claim Validation Requested" in xml_text
        assert "Claim Coordination Service" in xml_text
        assert "Validation Record" in xml_text
        assert "participates in" in xml_text
        assert "Application event triggers application interaction." in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass