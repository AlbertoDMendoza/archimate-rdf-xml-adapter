"""Convert ArchiMate Exchange XML directly to canonical Turtle-star RDF.

Unlike tools/import_xml_to_graphdb.py, this does not require a running
GraphDB instance: it builds the same canonical INSERT DATA triples and
serializes them straight to a .ttls file.

Relationships whose source or target is itself a relationship (e.g. an
Association pointing at another relationship, which the ArchiMate Exchange
format allows but the canonical RDF-star form has no resource for) are
skipped and reported, since the canonical form represents relationships as
triples rather than as addressable resources.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from archimate_adapter.dto.model import ModelDTO
from archimate_adapter.services.xml_to_rdf import (
    ElementTypeRegistry,
    RelationshipTypeRegistry,
    build_canonical_import_sparql,
)
from archimate_adapter.xml.parser import (
    NS,
    _assert_is_model_root,
    _parse_element,
    _parse_relationship,
)

DEFAULT_ELEMENT_MAPPING = Path("src/archimate_adapter/mapping/element_types.yaml")
DEFAULT_RELATIONSHIP_MAPPING = Path("src/archimate_adapter/mapping/relationship_types.yaml")


def parse_model_tolerant(path: Path) -> tuple[ModelDTO, list[str]]:
    root = ET.parse(path).getroot()
    _assert_is_model_root(root)

    model = ModelDTO()
    skipped: list[str] = []

    elements_parent = root.find("a:elements", NS)
    if elements_parent is not None:
        for element_el in elements_parent.findall("a:element", NS):
            model.add_element(_parse_element(element_el))

    relationships_parent = root.find("a:relationships", NS)
    if relationships_parent is not None:
        for rel_el in relationships_parent.findall("a:relationship", NS):
            relationship = _parse_relationship(rel_el)
            if not model.has_element(relationship.source_id) or not model.has_element(
                relationship.target_id
            ):
                skipped.append(
                    f"{relationship.identifier} ({relationship.xml_type}): "
                    f"source={relationship.source_id} target={relationship.target_id}"
                )
                continue
            model.add_relationship(relationship)

    return model, skipped


def sparql_insert_to_turtle(sparql: str) -> str:
    lines = sparql.splitlines()
    body_start = lines.index("INSERT DATA {") + 1
    body = lines[body_start:-1]
    prefixes = [
        line.replace("PREFIX", "@prefix", 1) + " ."
        for line in lines[: body_start - 1]
        if line.startswith("PREFIX")
    ]
    return "\n".join(prefixes) + "\n\n" + "\n".join(body) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_xml", type=Path)
    parser.add_argument("output_ttl", type=Path)
    parser.add_argument("--element-mapping", type=Path, default=DEFAULT_ELEMENT_MAPPING)
    parser.add_argument(
        "--relationship-mapping", type=Path, default=DEFAULT_RELATIONSHIP_MAPPING
    )
    args = parser.parse_args()

    model, skipped = parse_model_tolerant(args.input_xml)

    element_registry = ElementTypeRegistry.from_yaml(args.element_mapping)
    relationship_registry = RelationshipTypeRegistry.from_yaml(args.relationship_mapping)

    sparql = build_canonical_import_sparql(
        model=model,
        element_registry=element_registry,
        relationship_registry=relationship_registry,
        graph_iri=None,
    )
    turtle = sparql_insert_to_turtle(sparql)
    args.output_ttl.write_text(turtle, encoding="utf-8")

    print(f"Elements: {len(model.elements)}")
    print(f"Relationships: {len(model.relationships)}")
    print(f"Skipped relationships (endpoint is a relationship, not an element): {len(skipped)}")
    for entry in skipped:
        print(f"  - {entry}")
    print(f"Wrote {args.output_ttl}")


if __name__ == "__main__":
    main()
