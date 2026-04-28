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


def test_parse_model_with_application_process_event_business_object_batch():
    xml_text = """\
    <model xmlns="http://www.opengroup.org/xsd/archimate/3.0/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           identifier="model-1"
           version="1.0">
      <name xml:lang="en">Claim Handling Application Process Model</name>
      <elements>
        <element identifier="appcomp-1" xsi:type="ApplicationComponent">
          <name xml:lang="en">Claims Application</name>
          <documentation xml:lang="en">Application component that executes claim handling behavior.</documentation>
        </element>
        <element identifier="appproc-1" xsi:type="ApplicationProcess">
          <name xml:lang="en">Register Claim</name>
          <documentation xml:lang="en">Application process for registering incoming claims.</documentation>
        </element>
        <element identifier="appevt-1" xsi:type="ApplicationEvent">
          <name xml:lang="en">Claim Received</name>
          <documentation xml:lang="en">Application event raised when a claim is received.</documentation>
        </element>
        <element identifier="appsvc-1" xsi:type="ApplicationService">
          <name xml:lang="en">Claim Registration Service</name>
          <documentation xml:lang="en">Application service for claim registration.</documentation>
        </element>
        <element identifier="dataobj-1" xsi:type="DataObject">
          <name xml:lang="en">Claim Record</name>
          <documentation xml:lang="en">Application data object containing the registered claim.</documentation>
        </element>
        <element identifier="busobj-1" xsi:type="BusinessObject">
          <name xml:lang="en">Claim</name>
          <documentation xml:lang="en">Business object representing a claim.</documentation>
        </element>
        <element identifier="busproc-1" xsi:type="BusinessProcess">
          <name xml:lang="en">Handle Claim</name>
          <documentation xml:lang="en">Business process for handling a customer claim.</documentation>
        </element>
      </elements>
      <relationships>
        <relationship identifier="rel-10"
                      xsi:type="Assignment"
                      source="appcomp-1"
                      target="appproc-1">
          <name xml:lang="en">performs</name>
          <documentation xml:lang="en">Application component is assigned to the application process.</documentation>
        </relationship>
        <relationship identifier="rel-11"
                      xsi:type="Realization"
                      source="appproc-1"
                      target="appsvc-1">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Application process realizes application service.</documentation>
        </relationship>
        <relationship identifier="rel-12"
                      xsi:type="Triggering"
                      source="appevt-1"
                      target="appproc-1">
          <name xml:lang="en">triggers</name>
          <documentation xml:lang="en">Application event triggers application process.</documentation>
        </relationship>
        <relationship identifier="rel-13"
                      xsi:type="Access"
                      source="appproc-1"
                      target="dataobj-1">
          <name xml:lang="en">uses</name>
          <documentation xml:lang="en">Application process accesses claim record data.</documentation>
        </relationship>
        <relationship identifier="rel-14"
                      xsi:type="Realization"
                      source="dataobj-1"
                      target="busobj-1">
          <name xml:lang="en">realizes</name>
          <documentation xml:lang="en">Data object realizes business object.</documentation>
        </relationship>
        <relationship identifier="rel-15"
                      xsi:type="Serving"
                      source="appsvc-1"
                      target="busproc-1">
          <name xml:lang="en">serves</name>
          <documentation xml:lang="en">Application service serves business process.</documentation>
        </relationship>
      </relationships>
    </model>
    """

    model = parse_archimate_model_string(xml_text)

    assert len(model.elements) == 7
    assert len(model.relationships) == 6

    app_process = model.get_element("appproc-1")
    assert app_process.xml_type == "ApplicationProcess"
    assert app_process.name == "Register Claim"
    assert (
        app_process.documentation
        == "Application process for registering incoming claims."
    )

    app_event = model.get_element("appevt-1")
    assert app_event.xml_type == "ApplicationEvent"
    assert app_event.name == "Claim Received"
    assert (
        app_event.documentation
        == "Application event raised when a claim is received."
    )

    business_object = model.get_element("busobj-1")
    assert business_object.xml_type == "BusinessObject"
    assert business_object.name == "Claim"
    assert business_object.documentation == "Business object representing a claim."

    rel_triggering = next(r for r in model.relationships if r.identifier == "rel-12")
    assert rel_triggering.xml_type == "Triggering"
    assert rel_triggering.exchange_type == "Triggering"
    assert rel_triggering.source_id == "appevt-1"
    assert rel_triggering.target_id == "appproc-1"
    assert rel_triggering.name == "triggers"
    assert (
        rel_triggering.documentation
        == "Application event triggers application process."
    )


def test_build_canonical_import_sparql_with_application_process_event_business_object_batch():
    model = ModelDTO()
    model.add_element(
        ElementDTO(
            identifier="appcomp-1",
            xml_type="ApplicationComponent",
            name="Claims Application",
            documentation="Application component that executes claim handling behavior.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appproc-1",
            xml_type="ApplicationProcess",
            name="Register Claim",
            documentation="Application process for registering incoming claims.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appevt-1",
            xml_type="ApplicationEvent",
            name="Claim Received",
            documentation="Application event raised when a claim is received.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="appsvc-1",
            xml_type="ApplicationService",
            name="Claim Registration Service",
            documentation="Application service for claim registration.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="dataobj-1",
            xml_type="DataObject",
            name="Claim Record",
            documentation="Application data object containing the registered claim.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busobj-1",
            xml_type="BusinessObject",
            name="Claim",
            documentation="Business object representing a claim.",
        )
    )
    model.add_element(
        ElementDTO(
            identifier="busproc-1",
            xml_type="BusinessProcess",
            name="Handle Claim",
            documentation="Business process for handling a customer claim.",
        )
    )

    model.add_relationship(
        RelationshipDTO(
            identifier="rel-10",
            xml_type="Assignment",
            exchange_type="Assignment",
            source_id="appcomp-1",
            target_id="appproc-1",
            name="performs",
            documentation="Application component is assigned to the application process.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-11",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="appproc-1",
            target_id="appsvc-1",
            name="realizes",
            documentation="Application process realizes application service.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-12",
            xml_type="Triggering",
            exchange_type="Triggering",
            source_id="appevt-1",
            target_id="appproc-1",
            name="triggers",
            documentation="Application event triggers application process.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-13",
            xml_type="Access",
            exchange_type="Access",
            source_id="appproc-1",
            target_id="dataobj-1",
            name="uses",
            documentation="Application process accesses claim record data.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-14",
            xml_type="Realization",
            exchange_type="Realization",
            source_id="dataobj-1",
            target_id="busobj-1",
            name="realizes",
            documentation="Data object realizes business object.",
        )
    )
    model.add_relationship(
        RelationshipDTO(
            identifier="rel-15",
            xml_type="Serving",
            exchange_type="Serving",
            source_id="appsvc-1",
            target_id="busproc-1",
            name="serves",
            documentation="Application service serves business process.",
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

    assert "https://purl.org/archimate#ApplicationProcess" in sparql
    assert "https://purl.org/archimate#ApplicationEvent" in sparql
    assert "https://purl.org/archimate#BusinessObject" in sparql
    assert "https://purl.org/archimate#triggering" in sparql

    assert 'archimate:identifier "rel-10"' in sparql
    assert 'archimate:identifier "rel-11"' in sparql
    assert 'archimate:identifier "rel-12"' in sparql
    assert 'archimate:identifier "rel-13"' in sparql
    assert 'archimate:identifier "rel-14"' in sparql
    assert 'archimate:identifier "rel-15"' in sparql

    assert (
        "<< ex:appevt-1 <https://purl.org/archimate#triggering> ex:appproc-1 >>"
        in sparql
    )


@pytest.mark.integration
def test_import_from_file_inserts_application_process_event_business_object_batch_into_named_graph() -> None:
    graph_iri = "https://example.org/graph/test-import-application-process-event-business-object-batch"

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

    appcomp_iri = f"{EX_NS}appcomp-1"
    appproc_iri = f"{EX_NS}appproc-1"
    appevt_iri = f"{EX_NS}appevt-1"
    appsvc_iri = f"{EX_NS}appsvc-1"
    dataobj_iri = f"{EX_NS}dataobj-1"
    busobj_iri = f"{EX_NS}busobj-1"
    busproc_iri = f"{EX_NS}busproc-1"

    try:
        client.update(f"CLEAR GRAPH <{graph_iri}>")

        service.import_from_file(
            "tests/fixtures/xml/application_process_event_business_object_batch.xml"
        )

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{graph_iri}> {{
                <{appcomp_iri}> rdf:type archimate:ApplicationComponent .
                <{appproc_iri}> rdf:type archimate:ApplicationProcess .
                <{appevt_iri}> rdf:type archimate:ApplicationEvent .
                <{appsvc_iri}> rdf:type archimate:ApplicationService .
                <{dataobj_iri}> rdf:type archimate:DataObject .
                <{busobj_iri}> rdf:type archimate:BusinessObject .
                <{busproc_iri}> rdf:type archimate:BusinessProcess .

                <{appcomp_iri}> archimate:assignment <{appproc_iri}> .
                <{appproc_iri}> archimate:realization <{appsvc_iri}> .
                <{appevt_iri}> archimate:triggering <{appproc_iri}> .
                <{appproc_iri}> archimate:access <{dataobj_iri}> .
                <{dataobj_iri}> archimate:realization <{busobj_iri}> .
                <{appsvc_iri}> archimate:serving <{busproc_iri}> .

                << <{appcomp_iri}> archimate:assignment <{appproc_iri}> >>
                  archimate:identifier "rel-10" .
                << <{appproc_iri}> archimate:realization <{appsvc_iri}> >>
                  archimate:identifier "rel-11" .
                << <{appevt_iri}> archimate:triggering <{appproc_iri}> >>
                  archimate:identifier "rel-12" .
                << <{appproc_iri}> archimate:access <{dataobj_iri}> >>
                  archimate:identifier "rel-13" .
                << <{dataobj_iri}> archimate:realization <{busobj_iri}> >>
                  archimate:identifier "rel-14" .
                << <{appsvc_iri}> archimate:serving <{busproc_iri}> >>
                  archimate:identifier "rel-15" .
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


def test_export_canonical_rdf_to_xml_includes_application_process_event_business_object_batch(
    tmp_path: Path,
) -> None:
    graph_iri = "https://example.org/graph/test-export-application-process-event-business-object-batch"
    output_path = tmp_path / "exported-application-process-event-business-object-batch.xml"

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
            "tests/fixtures/xml/application_process_event_business_object_batch.xml"
        )
        export_service.export_to_file(str(output_path))

        assert output_path.exists()

        xml_text = output_path.read_text(encoding="utf-8")

        assert 'xsi:type="ApplicationProcess"' in xml_text
        assert 'xsi:type="ApplicationEvent"' in xml_text
        assert 'xsi:type="BusinessObject"' in xml_text
        assert 'xsi:type="Triggering"' in xml_text

        assert 'identifier="rel-10"' in xml_text
        assert 'identifier="rel-11"' in xml_text
        assert 'identifier="rel-12"' in xml_text
        assert 'identifier="rel-13"' in xml_text
        assert 'identifier="rel-14"' in xml_text
        assert 'identifier="rel-15"' in xml_text

        assert 'source="appcomp-1"' in xml_text
        assert 'target="appproc-1"' in xml_text
        assert 'source="appevt-1"' in xml_text
        assert 'source="appproc-1"' in xml_text
        assert 'target="dataobj-1"' in xml_text
        assert 'source="dataobj-1"' in xml_text
        assert 'target="busobj-1"' in xml_text
        assert 'source="appsvc-1"' in xml_text
        assert 'target="busproc-1"' in xml_text

        assert "Claims Application" in xml_text
        assert "Register Claim" in xml_text
        assert "Claim Received" in xml_text
        assert "Claim Registration Service" in xml_text
        assert "Claim Record" in xml_text
        assert "Claim" in xml_text
        assert "Handle Claim" in xml_text
        assert "triggers" in xml_text
        assert "Application event triggers application process." in xml_text

    finally:
        try:
            client.update(f"CLEAR GRAPH <{graph_iri}>")
        except GraphDBClientError:
            pass