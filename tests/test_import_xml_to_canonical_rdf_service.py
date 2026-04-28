import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace


class DummyClient:
    def __init__(self, *args, **kwargs):
        self.updates = []
        self.cleared_graphs = []

    def clear_graph(self, graph_iri: str) -> None:
        self.cleared_graphs.append(graph_iri)

    def update(self, query: str) -> None:
        self.updates.append(query)


class DummyIntegrityService:
    def __init__(self, client, element_registry, relationship_registry):
        self.client = client
        self.element_registry = element_registry
        self.relationship_registry = relationship_registry
        self.validated_graphs = []

    def assert_graph_is_valid(self, graph_iri: str) -> None:
        self.validated_graphs.append(graph_iri)


class RegistryStub:
    @classmethod
    def from_yaml(cls, path):
        return {"loaded_from": path}


# Build minimal fake package tree so the module under test can import successfully.
archimate_adapter_pkg = types.ModuleType("archimate_adapter")
graphdb_pkg = types.ModuleType("archimate_adapter.graphdb")
services_pkg = types.ModuleType("archimate_adapter.services")
xml_pkg = types.ModuleType("archimate_adapter.xml")

client_module = types.ModuleType("archimate_adapter.graphdb.client")
client_module.GraphDBClient = DummyClient

integrity_module = types.ModuleType(
    "archimate_adapter.services.assert_canonical_graph_integrity"
)
integrity_module.AssertCanonicalGraphIntegrityService = DummyIntegrityService

xml_to_rdf_module = types.ModuleType("archimate_adapter.services.xml_to_rdf")
xml_to_rdf_module.ElementTypeRegistry = RegistryStub
xml_to_rdf_module.RelationshipTypeRegistry = RegistryStub
xml_to_rdf_module.build_canonical_import_sparql = lambda **kwargs: "INSERT DATA {}"

parser_module = types.ModuleType("archimate_adapter.xml.parser")
parser_module.parse_archimate_model = lambda path: SimpleNamespace(name="dummy-model")

sys.modules["archimate_adapter"] = archimate_adapter_pkg
sys.modules["archimate_adapter.graphdb"] = graphdb_pkg
sys.modules["archimate_adapter.services"] = services_pkg
sys.modules["archimate_adapter.xml"] = xml_pkg
sys.modules["archimate_adapter.graphdb.client"] = client_module
sys.modules[
    "archimate_adapter.services.assert_canonical_graph_integrity"
] = integrity_module
sys.modules["archimate_adapter.services.xml_to_rdf"] = xml_to_rdf_module
sys.modules["archimate_adapter.xml.parser"] = parser_module

module_path = Path("/mnt/data/import_xml_to_canonical_rdf_updated.py")
spec = importlib.util.spec_from_file_location(
    "import_xml_to_canonical_rdf_updated",
    module_path,
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)
ImportXmlToCanonicalRdfService = module.ImportXmlToCanonicalRdfService


def test_import_uses_per_file_graph_without_clearing_when_append(monkeypatch, tmp_path):
    xml_path = tmp_path / "package A.xml"
    xml_path.write_text("<model/>", encoding="utf-8")

    dummy_client = DummyClient()
    integrity_instances = []

    monkeypatch.setattr(
        module,
        "parse_archimate_model",
        lambda path: SimpleNamespace(name="dummy-model"),
    )
    monkeypatch.setattr(module, "ElementTypeRegistry", RegistryStub)
    monkeypatch.setattr(module, "RelationshipTypeRegistry", RegistryStub)
    monkeypatch.setattr(module, "GraphDBClient", lambda **kwargs: dummy_client)

    def fake_integrity_factory(client, element_registry, relationship_registry):
        instance = DummyIntegrityService(client, element_registry, relationship_registry)
        integrity_instances.append(instance)
        return instance

    monkeypatch.setattr(module, "AssertCanonicalGraphIntegrityService", fake_integrity_factory)

    captured = {}

    def fake_build_canonical_import_sparql(
        model,
        element_registry,
        relationship_registry,
        graph_iri,
    ):
        captured["graph_iri"] = graph_iri
        return f"INSERT DATA {{ GRAPH <{graph_iri}> {{ }} }}"

    monkeypatch.setattr(module, "build_canonical_import_sparql", fake_build_canonical_import_sparql)

    service = ImportXmlToCanonicalRdfService(
        graphdb_base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
        element_mapping_path="elements.yaml",
        relationship_mapping_path="relationships.yaml",
        graph_iri="https://example.org/graph/model",
        replace_graph=False,
        graph_target_strategy="per_file",
        per_file_graph_base_iri="https://example.org/graph/model",
    )

    imported_graph_iri = service.import_from_file(xml_path)

    assert imported_graph_iri == "https://example.org/graph/model/package%20A"
    assert captured["graph_iri"] == imported_graph_iri
    assert dummy_client.cleared_graphs == []
    assert dummy_client.updates == [
        "INSERT DATA { GRAPH <https://example.org/graph/model/package%20A> { } }"
    ]
    assert integrity_instances[0].validated_graphs == [imported_graph_iri]


def test_import_clears_single_graph_when_replace_enabled(monkeypatch, tmp_path):
    xml_path = tmp_path / "package-b.xml"
    xml_path.write_text("<model/>", encoding="utf-8")

    dummy_client = DummyClient()

    monkeypatch.setattr(
        module,
        "parse_archimate_model",
        lambda path: SimpleNamespace(name="dummy-model"),
    )
    monkeypatch.setattr(module, "ElementTypeRegistry", RegistryStub)
    monkeypatch.setattr(module, "RelationshipTypeRegistry", RegistryStub)
    monkeypatch.setattr(module, "GraphDBClient", lambda **kwargs: dummy_client)
    monkeypatch.setattr(
        module,
        "AssertCanonicalGraphIntegrityService",
        lambda client, element_registry, relationship_registry: DummyIntegrityService(
            client, element_registry, relationship_registry
        ),
    )
    monkeypatch.setattr(
        module,
        "build_canonical_import_sparql",
        lambda **kwargs: "INSERT DATA { GRAPH <https://example.org/graph/model> { } }",
    )

    service = ImportXmlToCanonicalRdfService(
        graphdb_base_url=GRAPHDB_BASE_URL,
        repository_id="archimate_phase1",
        element_mapping_path="elements.yaml",
        relationship_mapping_path="relationships.yaml",
        graph_iri="https://example.org/graph/model",
        replace_graph=True,
        graph_target_strategy="single",
    )

    imported_graph_iri = service.import_from_file(xml_path)

    assert imported_graph_iri == "https://example.org/graph/model"
    assert dummy_client.cleared_graphs == ["https://example.org/graph/model"]
    assert dummy_client.updates == [
        "INSERT DATA { GRAPH <https://example.org/graph/model> { } }"
    ]
