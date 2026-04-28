from pathlib import Path

GRAPHDB_BASE_URL = "http://localhost:7200"
GRAPHDB_REPOSITORY_ID = "archimate_phase1"
DEFAULT_MODEL_GRAPH_IRI = "https://example.org/graph/model"

# Import behavior
# - IMPORT_MODE = "replace": clear the target graph before import
# - IMPORT_MODE = "append": keep existing data in the target graph
IMPORT_MODE = "replace"

# Graph targeting behavior
# - GRAPH_TARGET_STRATEGY = "single": always import into DEFAULT_MODEL_GRAPH_IRI
# - GRAPH_TARGET_STRATEGY = "per_file": derive a dedicated named graph per XML file
GRAPH_TARGET_STRATEGY = "per_file"

# Base IRI used when GRAPH_TARGET_STRATEGY == "per_file"
PER_FILE_GRAPH_BASE_IRI = DEFAULT_MODEL_GRAPH_IRI

ELEMENT_MAPPING_PATH = Path("src/archimate_adapter/mapping/element_types.yaml")
RELATIONSHIP_MAPPING_PATH = Path("src/archimate_adapter/mapping/relationship_types.yaml")

DEFAULT_IMPORT_XML_PATH = Path("out/RVO/GLB23-27_42.xml")
DEFAULT_EXPORT_XML_PATH = Path("out/exported-from-graphdb.xml")
