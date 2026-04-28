from pathlib import Path

import pytest

from archimate_adapter.graphdb.client import GraphDBClient, GraphDBClientError
from archimate_adapter.namespaces import ARCHIMATE_NS, EX_NS, RDF_NS
from archimate_adapter.services.export_canonical_rdf_to_xml import (
    ExportCanonicalRdfToXmlService,
)
from archimate_adapter.services.import_xml_to_canonical_rdf import (
    ImportXmlToCanonicalRdfService,
)


@pytest.mark.integration
def test_roundtrip_supported_phase1_types(tmp_path: Path) -> None:
    source_graph_iri = "https://example.org/graph/test-roundtrip-phase1-source"
    roundtrip_graph_iri = "https://example.org/graph/test-roundtrip-phase1-roundtrip"
    exported_xml_path = tmp_path / "phase1-supported-types-roundtrip.xml"

    client = GraphDBClient(
        base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
    )

    source_import_service = ImportXmlToCanonicalRdfService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=source_graph_iri,
    )

    export_service = ExportCanonicalRdfToXmlService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=source_graph_iri,
    )

    roundtrip_import_service = ImportXmlToCanonicalRdfService(
        graphdb_base_url="http://192.168.0.105:7200",
        repository_id="archimate_phase1",
        element_mapping_path="src/archimate_adapter/mapping/element_types.yaml",
        relationship_mapping_path="src/archimate_adapter/mapping/relationship_types.yaml",
        graph_iri=roundtrip_graph_iri,
    )

    app_iri = f"{EX_NS}app-1"
    actor_iri = f"{EX_NS}actor-1"
    process_iri = f"{EX_NS}process-1"
    appsvc_iri = f"{EX_NS}appsvc-1"
    data_iri = f"{EX_NS}data-1"
    appfn_iri = f"{EX_NS}appfn-1"
    appi_iri = f"{EX_NS}appi-1"

    role_iri = f"{EX_NS}role-1"
    busfn_iri = f"{EX_NS}busfn-1"
    bussvc_iri = f"{EX_NS}bussvc-1"

    appcomp1_iri = f"{EX_NS}appcomp-1"
    appproc_iri = f"{EX_NS}appproc-1"
    appevt1_iri = f"{EX_NS}appevt-1"
    dataobj1_iri = f"{EX_NS}dataobj-1"
    busobj1_iri = f"{EX_NS}busobj-1"
    busproc1_iri = f"{EX_NS}busproc-1"

    appcomp2_iri = f"{EX_NS}appcomp-2"
    appcomp3_iri = f"{EX_NS}appcomp-3"
    appcollab_iri = f"{EX_NS}appcollab-1"
    appint_iri = f"{EX_NS}appint-1"
    appevt2_iri = f"{EX_NS}appevt-2"
    appsvc2_iri = f"{EX_NS}appsvc-2"
    dataobj2_iri = f"{EX_NS}dataobj-2"

    buscollab_iri = f"{EX_NS}buscollab-1"
    role2_iri = f"{EX_NS}role-2"
    actor2_iri = f"{EX_NS}actor-2"
    busint_iri = f"{EX_NS}busint-1"
    busevt_iri = f"{EX_NS}busevt-1"
    bussvc2_iri = f"{EX_NS}bussvc-2"
    busobj2_iri = f"{EX_NS}busobj-2"

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
    technode_iri = f"{EX_NS}technode-1"
    device_iri = f"{EX_NS}device-1"
    syssoft_iri = f"{EX_NS}syssoft-1"
    techif_iri = f"{EX_NS}techif-1"
    techsvc_iri = f"{EX_NS}techsvc-1"
    techcollab_iri = f"{EX_NS}techcollab-1"
    techevt_iri = f"{EX_NS}techevt-1"
    techfn_iri = f"{EX_NS}techfn-1"
    techint_iri = f"{EX_NS}techint-1"
    techproc_iri = f"{EX_NS}techproc-1"
    artifact_iri = f"{EX_NS}artifact-1"
    commnet_iri = f"{EX_NS}commnet-1"
    equipment_iri = f"{EX_NS}equipment-1"
    facility_iri = f"{EX_NS}facility-1"
    assessment_iri = f"{EX_NS}assessment-1"
    principle_iri = f"{EX_NS}principle-1"
    constraint_iri = f"{EX_NS}constraint-1"
    meaning_iri = f"{EX_NS}meaning-1"
    material_iri = f"{EX_NS}material-1"
    distribution_iri = f"{EX_NS}distribution-1"
    stakeholder_iri = f"{EX_NS}stakeholder-1"
    driver_iri = f"{EX_NS}driver-1"
    goal_iri = f"{EX_NS}goal-1"
    requirement_iri = f"{EX_NS}requirement-1"
    value_iri = f"{EX_NS}value-1"
    capability_iri = f"{EX_NS}capability-1"
    courseofaction_iri = f"{EX_NS}courseofaction-1"
    deliverable_iri = f"{EX_NS}deliverable-1"
    gap_iri = f"{EX_NS}gap-1"
    grouping_iri = f"{EX_NS}grouping-1"
    implementationevent_iri = f"{EX_NS}implementationevent-1"
    location_iri = f"{EX_NS}location-1"
    outcome_iri = f"{EX_NS}outcome-1"
    path_iri = f"{EX_NS}path-1"
    plateau_iri = f"{EX_NS}plateau-1"
    resource_iri = f"{EX_NS}resource-1"
    valuestream_iri = f"{EX_NS}valuestream-1"
    workpackage_iri = f"{EX_NS}workpackage-1"

    try:
        client.update(f"CLEAR GRAPH <{source_graph_iri}>")
        client.update(f"CLEAR GRAPH <{roundtrip_graph_iri}>")

        source_import_service.import_from_file(
            "tests/fixtures/xml/phase1_supported_types.xml"
        )

        export_service.export_to_file(str(exported_xml_path))

        assert exported_xml_path.exists()

        exported_xml = exported_xml_path.read_text(encoding="utf-8")

        # All currently supported element types
        for xml_type in [
            "ApplicationCollaboration",
            "ApplicationComponent",
            "ApplicationEvent",
            "ApplicationFunction",
            "ApplicationInteraction",
            "ApplicationInterface",
            "ApplicationProcess",
            "ApplicationService",
            "BusinessActor",
            "BusinessCollaboration",
            "Contract",
            "BusinessEvent",
            "BusinessFunction",
            "BusinessInteraction",
            "BusinessInterface",
            "BusinessObject",
            "BusinessProcess",
            "BusinessRole",
            "BusinessService",
            "DataObject",
            "Product",
            "Representation",
            "Node",
            "Device",
            "SystemSoftware",
            "TechnologyInterface",
            "TechnologyService",
            "TechnologyCollaboration",
            "TechnologyEvent",
            "TechnologyFunction",
            "TechnologyInteraction",
            "TechnologyProcess",
            "Artifact",
            "CommunicationNetwork",
            "Equipment",
            "Facility",
            "Material",
            "DistributionNetwork",
            "Stakeholder",
            "Driver",
            "Assessment",
            "Principle",
            "Constraint",
            "Meaning",
            "Goal",
            "Requirement",
            "Value",
            "Capability",
            "CourseOfAction",
            "Deliverable",
            "Gap",
            "Grouping",
            "ImplementationEvent",
            "Location",
            "Outcome",
            "Path",
            "Plateau",
            "Resource",
            "ValueStream",
            "WorkPackage",
            "AndJunction",
            "OrJunction",
        ]:
            assert f'xsi:type="{xml_type}"' in exported_xml

        # All currently supported relationship types
        for rel_type in [
            "Serving",
            "Assignment",
            "Realization",
            "Access",
            "Composition",
            "Triggering",
            "Aggregation",
            "Association",
            "Flow",
            "Influence",
            "Specialization",
        ]:
            assert f'xsi:type="{rel_type}"' in exported_xml

        # Representative identifiers from all batches
        for identifier in [
            "app-1",
            "actor-1",
            "process-1",
            "appsvc-1",
            "data-1",
            "appfn-1",
            "appi-1",
            "role-1",
            "busfn-1",
            "bussvc-1",
            "appcomp-1",
            "appproc-1",
            "appevt-1",
            "dataobj-1",
            "busobj-1",
            "busproc-1",
            "appcomp-2",
            "appcomp-3",
            "appcollab-1",
            "appint-1",
            "appevt-2",
            "appsvc-2",
            "dataobj-2",
            "buscollab-1",
            "role-2",
            "actor-2",
            "busint-1",
            "busevt-1",
            "bussvc-2",
            "busobj-2",
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
            "technode-1",
            "device-1",
            "syssoft-1",
            "techif-1",
            "techsvc-1",
            "techcollab-1",
            "techevt-1",
            "techfn-1",
            "techint-1",
            "techproc-1",
            "artifact-1",
            "commnet-1",
            "equipment-1",
            "facility-1",
            "material-1",
            "distribution-1",
            "stakeholder-1",
            "driver-1",
            "assessment-1",
            "principle-1",
            "constraint-1",
            "meaning-1",
            "goal-1",
            "requirement-1",
            "value-1",
            "capability-1",
            "courseofaction-1",
            "deliverable-1",
            "gap-1",
            "grouping-1",
            "implementationevent-1",
            "location-1",
            "outcome-1",
            "path-1",
            "plateau-1",
            "resource-1",
            "valuestream-1",
            "workpackage-1",
            "and-junction-1",
            "or-junction-1",
        ]:
            assert f'identifier="{identifier}"' in exported_xml

        for rel_id in [
            "rel-1",
            "rel-2",
            "rel-3",
            "rel-4",
            "rel-5",
            "rel-6",
            "rel-8",
            "rel-9",
            "rel-10",
            "rel-11",
            "rel-12",
            "rel-13",
            "rel-14",
            "rel-15",
            "rel-16",
            "rel-17",
            "rel-18",
            "rel-19",
            "rel-20",
            "rel-21",
            "rel-22",
            "rel-23",
            "rel-24",
            "rel-25",
            "rel-26",
            "rel-27",
            "rel-28",
            "rel-29",
            "rel-30",
            "rel-31",
            "rel-32",
            "rel-33",
            "rel-34",
            "rel-35",
            "rel-36",
            "rel-37",
            "rel-38",
            "rel-39",
            "rel-40",
            "rel-41",
            "rel-42",
            "rel-43",
            "rel-44",
            "rel-45",
            "rel-46",
            "rel-47",
            "rel-48",
            "rel-49",
        ]:
            assert f'identifier="{rel_id}"' in exported_xml

        roundtrip_import_service.import_from_file(str(exported_xml_path))

        result = client.ask(
            f"""
            PREFIX rdf: <{RDF_NS}>
            PREFIX archimate: <{ARCHIMATE_NS}>

            ASK {{
              GRAPH <{roundtrip_graph_iri}> {{
                <{app_iri}> rdf:type archimate:ApplicationComponent .
                <{actor_iri}> rdf:type archimate:BusinessActor .
                <{process_iri}> rdf:type archimate:BusinessProcess .
                <{appsvc_iri}> rdf:type archimate:ApplicationService .
                <{data_iri}> rdf:type archimate:DataObject .
                <{appfn_iri}> rdf:type archimate:ApplicationFunction .
                <{appi_iri}> rdf:type archimate:ApplicationInterface .

                <{role_iri}> rdf:type archimate:BusinessRole .
                <{busfn_iri}> rdf:type archimate:BusinessFunction .
                <{bussvc_iri}> rdf:type archimate:BusinessService .

                <{appcomp1_iri}> rdf:type archimate:ApplicationComponent .
                <{appproc_iri}> rdf:type archimate:ApplicationProcess .
                <{appevt1_iri}> rdf:type archimate:ApplicationEvent .
                <{dataobj1_iri}> rdf:type archimate:DataObject .
                <{busobj1_iri}> rdf:type archimate:BusinessObject .
                <{busproc1_iri}> rdf:type archimate:BusinessProcess .

                <{appcomp2_iri}> rdf:type archimate:ApplicationComponent .
                <{appcomp3_iri}> rdf:type archimate:ApplicationComponent .
                <{appcollab_iri}> rdf:type archimate:ApplicationCollaboration .
                <{appint_iri}> rdf:type archimate:ApplicationInteraction .
                <{appevt2_iri}> rdf:type archimate:ApplicationEvent .
                <{appsvc2_iri}> rdf:type archimate:ApplicationService .
                <{dataobj2_iri}> rdf:type archimate:DataObject .

                <{buscollab_iri}> rdf:type archimate:BusinessCollaboration .
                <{role2_iri}> rdf:type archimate:BusinessRole .
                <{actor2_iri}> rdf:type archimate:BusinessActor .
                <{busint_iri}> rdf:type archimate:BusinessInteraction .
                <{busevt_iri}> rdf:type archimate:BusinessEvent .
                <{bussvc2_iri}> rdf:type archimate:BusinessService .
                <{busobj2_iri}> rdf:type archimate:BusinessObject .

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
                <{technode_iri}> rdf:type archimate:Node .
                <{device_iri}> rdf:type archimate:Device .
                <{syssoft_iri}> rdf:type archimate:SystemSoftware .
                <{techif_iri}> rdf:type archimate:TechnologyInterface .
                <{techsvc_iri}> rdf:type archimate:TechnologyService .
                <{techcollab_iri}> rdf:type archimate:TechnologyCollaboration .
                <{techevt_iri}> rdf:type archimate:TechnologyEvent .
                <{techfn_iri}> rdf:type archimate:TechnologyFunction .
                <{techint_iri}> rdf:type archimate:TechnologyInteraction .
                <{techproc_iri}> rdf:type archimate:TechnologyProcess .
                <{artifact_iri}> rdf:type archimate:Artifact .
                <{commnet_iri}> rdf:type archimate:CommunicationNetwork .
                <{equipment_iri}> rdf:type archimate:Equipment .
                <{facility_iri}> rdf:type archimate:Facility .
                <{material_iri}> rdf:type archimate:Material .
                <{distribution_iri}> rdf:type archimate:DistributionNetwork .
                <{stakeholder_iri}> rdf:type archimate:Stakeholder .
                <{driver_iri}> rdf:type archimate:Driver .
                <{assessment_iri}> rdf:type archimate:Assessment .
                <{principle_iri}> rdf:type archimate:Principle .
                <{constraint_iri}> rdf:type archimate:Constraint .
                <{meaning_iri}> rdf:type archimate:Meaning .
                <{goal_iri}> rdf:type archimate:Goal .
                <{requirement_iri}> rdf:type archimate:Requirement .
                <{value_iri}> rdf:type archimate:Value .
                <{capability_iri}> rdf:type archimate:Capability .
                <{courseofaction_iri}> rdf:type archimate:CourseOfAction .
                <{deliverable_iri}> rdf:type archimate:Deliverable .
                <{gap_iri}> rdf:type archimate:Gap .
                <{grouping_iri}> rdf:type archimate:Grouping .
                <{implementationevent_iri}> rdf:type archimate:ImplementationEvent .
                <{location_iri}> rdf:type archimate:Location .
                <{outcome_iri}> rdf:type archimate:Outcome .
                <{path_iri}> rdf:type archimate:Path .
                <{plateau_iri}> rdf:type archimate:Plateau .
                <{resource_iri}> rdf:type archimate:Resource .
                <{valuestream_iri}> rdf:type archimate:ValueStream .
                <{workpackage_iri}> rdf:type archimate:WorkPackage .
                <{EX_NS}and-junction-1> rdf:type archimate:Junction ;
                  archimate:junctionType "and" .
                <{EX_NS}or-junction-1> rdf:type archimate:Junction ;
                  archimate:junctionType "or" .

                <{app_iri}> archimate:serving <{actor_iri}> .
                <{actor_iri}> archimate:assignment <{process_iri}> .
                <{app_iri}> archimate:realization <{appsvc_iri}> .
                <{app_iri}> archimate:access <{data_iri}> .
                <{appfn_iri}> archimate:realization <{appsvc_iri}> .
                <{app_iri}> archimate:composition <{appi_iri}> .

                <{busfn_iri}> archimate:realization <{bussvc_iri}> .
                <{role_iri}> archimate:assignment <{busfn_iri}> .

                <{appcomp1_iri}> archimate:assignment <{appproc_iri}> .
                <{appproc_iri}> archimate:realization <{appsvc_iri}> .
                <{appevt1_iri}> archimate:triggering <{appproc_iri}> .
                <{appproc_iri}> archimate:access <{dataobj1_iri}> .
                <{dataobj1_iri}> archimate:realization <{busobj1_iri}> .
                <{appsvc_iri}> archimate:serving <{busproc1_iri}> .

                <{appcollab_iri}> archimate:aggregation <{appcomp2_iri}> .
                <{appcollab_iri}> archimate:aggregation <{appcomp3_iri}> .
                <{appcollab_iri}> archimate:assignment <{appint_iri}> .
                <{appint_iri}> archimate:realization <{appsvc2_iri}> .
                <{appint_iri}> archimate:access <{dataobj2_iri}> .
                <{appevt2_iri}> archimate:triggering <{appint_iri}> .

                <{buscollab_iri}> archimate:aggregation <{role2_iri}> .
                <{buscollab_iri}> archimate:aggregation <{actor2_iri}> .
                <{buscollab_iri}> archimate:assignment <{busint_iri}> .
                <{busint_iri}> archimate:realization <{bussvc2_iri}> .
                <{busint_iri}> archimate:access <{busobj2_iri}> .
                <{busevt_iri}> archimate:triggering <{busint_iri}> .

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
                <{device_iri}> archimate:realization <{techsvc_iri}> .
                <{techcollab_iri}> archimate:aggregation <{device_iri}> .
                <{commnet_iri}> archimate:aggregation <{techif_iri}> .
                <{equipment_iri}> archimate:access <{material_iri}> .
                <{distribution_iri}> archimate:flow <{equipment_iri}> .
                <{driver_iri}> archimate:influence <{goal_iri}> .
                <{requirement_iri}> archimate:realization <{goal_iri}> .
                <{stakeholder_iri}> archimate:association <{goal_iri}> .
                <{busevt_iri}> archimate:triggering <{EX_NS}and-junction-1> .
                <{EX_NS}and-junction-1> archimate:triggering <{busproc2_iri}> .
                <{appevt2_iri}> archimate:triggering <{EX_NS}or-junction-1> .
                <{EX_NS}or-junction-1> archimate:triggering <{busproc3_iri}> .

                << <{app_iri}> archimate:serving <{actor_iri}> >>
                  archimate:identifier "rel-1" .
                << <{actor_iri}> archimate:assignment <{process_iri}> >>
                  archimate:identifier "rel-2" .
                << <{app_iri}> archimate:realization <{appsvc_iri}> >>
                  archimate:identifier "rel-3" .
                << <{app_iri}> archimate:access <{data_iri}> >>
                  archimate:identifier "rel-4" .
                << <{appfn_iri}> archimate:realization <{appsvc_iri}> >>
                  archimate:identifier "rel-5" .
                << <{app_iri}> archimate:composition <{appi_iri}> >>
                  archimate:identifier "rel-6" .

                << <{busfn_iri}> archimate:realization <{bussvc_iri}> >>
                  archimate:identifier "rel-8" .
                << <{role_iri}> archimate:assignment <{busfn_iri}> >>
                  archimate:identifier "rel-9" .

                << <{appcomp1_iri}> archimate:assignment <{appproc_iri}> >>
                  archimate:identifier "rel-10" .
                << <{appproc_iri}> archimate:realization <{appsvc_iri}> >>
                  archimate:identifier "rel-11" .
                << <{appevt1_iri}> archimate:triggering <{appproc_iri}> >>
                  archimate:identifier "rel-12" .
                << <{appproc_iri}> archimate:access <{dataobj1_iri}> >>
                  archimate:identifier "rel-13" .
                << <{dataobj1_iri}> archimate:realization <{busobj1_iri}> >>
                  archimate:identifier "rel-14" .
                << <{appsvc_iri}> archimate:serving <{busproc1_iri}> >>
                  archimate:identifier "rel-15" .

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
                << <{device_iri}> archimate:realization <{techsvc_iri}> >>
                  archimate:identifier "rel-38" .
                << <{techcollab_iri}> archimate:aggregation <{device_iri}> >>
                  archimate:identifier "rel-39" .
                << <{commnet_iri}> archimate:aggregation <{techif_iri}> >>
                  archimate:identifier "rel-40" .
                << <{equipment_iri}> archimate:access <{material_iri}> >>
                  archimate:identifier "rel-41" .
                << <{distribution_iri}> archimate:flow <{equipment_iri}> >>
                  archimate:identifier "rel-42" .
                << <{driver_iri}> archimate:influence <{goal_iri}> >>
                  archimate:identifier "rel-43" .
                << <{requirement_iri}> archimate:realization <{goal_iri}> >>
                  archimate:identifier "rel-44" .
                << <{stakeholder_iri}> archimate:association <{goal_iri}> >>
                  archimate:identifier "rel-45" .
                << <{busevt_iri}> archimate:triggering <{EX_NS}and-junction-1> >>
                  archimate:identifier "rel-46" .
                << <{EX_NS}and-junction-1> archimate:triggering <{busproc2_iri}> >>
                  archimate:identifier "rel-47" .
                << <{appevt2_iri}> archimate:triggering <{EX_NS}or-junction-1> >>
                  archimate:identifier "rel-48" .
                << <{EX_NS}or-junction-1> archimate:triggering <{busproc3_iri}> >>
                  archimate:identifier "rel-49" .
              }}
            }}
            """
        )

        assert result is True

    finally:
        try:
            client.update(f"CLEAR GRAPH <{source_graph_iri}>")
        except GraphDBClientError:
            pass

        try:
            client.update(f"CLEAR GRAPH <{roundtrip_graph_iri}>")
        except GraphDBClientError:
            pass