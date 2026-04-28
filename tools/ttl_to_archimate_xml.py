"""
Convert a Mendoza-style ArchiMate TTL file to ArchiMate Exchange XML.

Dynamically resolves specialization types to standard ArchiMate element types
by walking rdfs:subClassOf chains, and resolves custom relationship predicates
by walking rdfs:subPropertyOf chains. No framework-specific types are hardcoded.

Collects all literal-valued properties on each instance and emits them as
ArchiMate Exchange XML propertyDefinitions / properties.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
import rdflib
from rdflib import RDF, RDFS, OWL, Namespace, Literal, URIRef

ARCHIMATE_RDF_NS = "https://purl.org/archimate#"
ARCHIMATE = Namespace(ARCHIMATE_RDF_NS)
DCT = Namespace("http://purl.org/dc/terms/")

# Predicates to skip when collecting specialization properties
SKIP_PREDICATES = {
    str(RDF.type),
    str(RDFS.label),
    str(RDFS.comment),
    str(OWL.imports),
    str(OWL.versionInfo),
    str(ARCHIMATE.identifier),
    str(ARCHIMATE["name"]),
    str(DCT.description),
    str(DCT.created),
    str(DCT.creator),
    str(DCT.modified),
}


@dataclass
class ElementInfo:
    identifier: str
    xml_type: str
    original_type: str
    name: str | None = None
    documentation: str | None = None
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class RelInfo:
    identifier: str
    xml_type: str
    source_id: str
    target_id: str


def _load_known_element_types(yaml_path: Path) -> dict[str, str]:
    """Load rdf_class -> xml_type mapping from the adapter's element_types.yaml."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return {v["rdf_class"]: k for k, v in data.get("xml_to_rdf", {}).items()}


def _load_known_rel_predicates(yaml_path: Path) -> dict[str, str]:
    """Load rdf_predicate -> xml_type mapping from the adapter's relationship_types.yaml."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return {v["rdf_predicate"]: v.get("exchange_type", k)
            for k, v in data.get("xml_to_rdf", {}).items()}


def _resolve_type(rdf_type: str, g: rdflib.Graph,
                  known_types: dict[str, str],
                  _seen: set[str] | None = None) -> str | None:
    """Walk rdfs:subClassOf chain to find the nearest known ArchiMate type."""
    if rdf_type in known_types:
        return known_types[rdf_type]
    if _seen is None:
        _seen = set()
    if rdf_type in _seen:
        return None
    _seen.add(rdf_type)
    for parent in g.objects(URIRef(rdf_type), RDFS.subClassOf):
        result = _resolve_type(str(parent), g, known_types, _seen)
        if result:
            return result
    return None


def _resolve_predicate(pred: str, g: rdflib.Graph,
                       known_preds: dict[str, str],
                       _seen: set[str] | None = None) -> str | None:
    """Walk rdfs:subPropertyOf chain to find the nearest known ArchiMate predicate."""
    if pred in known_preds:
        return known_preds[pred]
    if _seen is None:
        _seen = set()
    if pred in _seen:
        return None
    _seen.add(pred)
    for parent in g.objects(URIRef(pred), RDFS.subPropertyOf):
        result = _resolve_predicate(str(parent), g, known_preds, _seen)
        if result:
            return result
    return None


def _short_type(rdf_type: str) -> str:
    """Return a readable short form for an RDF type URI."""
    if "#" in rdf_type:
        return rdf_type.rsplit("#", 1)[1]
    if "/" in rdf_type:
        return rdf_type.rsplit("/", 1)[1]
    return rdf_type


def convert(ttl_path: str | Path, output_path: str | Path,
            element_yaml: str | Path | None = None,
            rel_yaml: str | Path | None = None) -> None:
    # Resolve mapping YAML paths
    base = Path(__file__).resolve().parent.parent / "src" / "archimate_adapter" / "mapping"
    elem_yaml = Path(element_yaml) if element_yaml else base / "element_types.yaml"
    r_yaml = Path(rel_yaml) if rel_yaml else base / "relationship_types.yaml"

    known_types = _load_known_element_types(elem_yaml)
    known_preds = _load_known_rel_predicates(r_yaml)

    g = rdflib.Graph()
    g.parse(str(ttl_path), format="turtle")

    # Collect all subjects with archimate:identifier
    id_map: dict[str, str] = {}
    for s, _p, o in g.triples((None, ARCHIMATE.identifier, None)):
        id_map[str(s)] = str(o)

    # Build elements
    elements: dict[str, ElementInfo] = {}
    skipped: list[str] = []

    for uri, arch_id in id_map.items():
        uri_ref = URIRef(uri)

        # Find rdf:type and resolve to ArchiMate XML type
        xml_type = None
        original_type = None
        for _s, _p, type_obj in g.triples((uri_ref, RDF.type, None)):
            type_str = str(type_obj)
            resolved = _resolve_type(type_str, g, known_types)
            if resolved:
                xml_type = resolved
                original_type = type_str
                break

        if xml_type is None:
            skipped.append(f"{arch_id} (unresolvable type)")
            continue

        # Get name and documentation
        name = None
        for _s, _p, v in g.triples((uri_ref, ARCHIMATE["name"], None)):
            name = str(v)
            break

        doc = None
        for _s, _p, v in g.triples((uri_ref, DCT.description, None)):
            doc = str(v)
            break

        # Collect all literal-valued properties (skip standard ones)
        props: dict[str, str] = {}
        if original_type and original_type not in known_types:
            props["Specialization"] = _short_type(original_type)

        for _s, pred, obj in g.triples((uri_ref, None, None)):
            pred_str = str(pred)
            if pred_str in SKIP_PREDICATES:
                continue
            if not isinstance(obj, Literal):
                continue
            # Use short predicate name as property key
            prop_name = _short_type(pred_str)
            props[prop_name] = str(obj)

        elements[uri] = ElementInfo(
            identifier=arch_id,
            xml_type=xml_type,
            original_type=original_type or "",
            name=name,
            documentation=doc,
            properties=props,
        )

    # Build relationships — scan all predicates between known elements
    relationships: list[RelInfo] = []
    rel_counter = 0
    seen_rels: set[tuple[str, str, str]] = set()

    for s, p, o in g:
        s_uri, p_str, o_uri = str(s), str(p), str(o)
        if s_uri not in elements or o_uri not in elements:
            continue
        if not isinstance(o, URIRef):
            continue

        rel_type = _resolve_predicate(p_str, g, known_preds)
        if rel_type is None:
            continue

        key = (s_uri, p_str, o_uri)
        if key in seen_rels:
            continue
        seen_rels.add(key)

        rel_counter += 1
        relationships.append(RelInfo(
            identifier=f"rel-{rel_counter:04d}",
            xml_type=rel_type,
            source_id=elements[s_uri].identifier,
            target_id=elements[o_uri].identifier,
        ))

    # Collect property definitions
    sorted_elements = sorted(elements.values(), key=lambda e: e.identifier)
    all_prop_names: set[str] = set()
    for elem in sorted_elements:
        all_prop_names.update(elem.properties.keys())
    prop_names = sorted(all_prop_names)
    propdef_ids = {name: f"propdef-{i:03d}" for i, name in enumerate(prop_names, 1)}

    # Write XML
    model_name = Path(ttl_path).stem
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_xml(sorted_elements, relationships, propdef_ids, prop_names,
               output, model_name)

    print(f"Converted: {len(sorted_elements)} elements, {len(relationships)} relationships")
    print(f"Property definitions: {len(prop_names)}")
    if skipped:
        print(f"Skipped: {len(skipped)} (no resolvable ArchiMate type)")
        for s in skipped:
            print(f"  - {s}")
    print(f"Output: {output_path}")


def _write_xml(
    elements: list[ElementInfo],
    relationships: list[RelInfo],
    propdef_ids: dict[str, str],
    prop_names: list[str],
    output_path: Path,
    model_name: str,
) -> None:
    ARCHIMATE_XML_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    SCHEMA_LOC = (f"{ARCHIMATE_XML_NS} "
                  "http://www.opengroup.org/xsd/archimate/3.1/archimate3_Model.xsd")

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<model xmlns="{ARCHIMATE_XML_NS}"')
    lines.append(f'       xmlns:xsi="{XSI_NS}"')
    lines.append('       identifier="model-1"')
    lines.append('       version="1.0"')
    lines.append(f'       xsi:schemaLocation="{SCHEMA_LOC}">')
    lines.append(f'  <name xml:lang="en">{_esc(model_name)}</name>')

    # Elements
    lines.append('  <elements>')
    for elem in elements:
        lines.append(f'    <element identifier="{_esc(elem.identifier)}"'
                     f' xsi:type="{_esc(elem.xml_type)}">')
        if elem.name:
            lines.append(f'      <name xml:lang="en">{_esc(elem.name)}</name>')
        if elem.documentation:
            lines.append(f'      <documentation xml:lang="en">'
                         f'{_esc(elem.documentation)}</documentation>')
        if elem.properties:
            lines.append('      <properties>')
            for pname in sorted(elem.properties.keys()):
                pid = propdef_ids[pname]
                val = elem.properties[pname]
                lines.append(f'        <property propertyDefinitionRef="{pid}">')
                lines.append(f'          <value xml:lang="en">{_esc(val)}</value>')
                lines.append('        </property>')
            lines.append('      </properties>')
        lines.append('    </element>')
    lines.append('  </elements>')

    # Relationships
    lines.append('  <relationships>')
    for rel in relationships:
        lines.append(
            f'    <relationship identifier="{_esc(rel.identifier)}"'
            f' source="{_esc(rel.source_id)}"'
            f' target="{_esc(rel.target_id)}"'
            f' xsi:type="{_esc(rel.xml_type)}" />'
        )
    lines.append('  </relationships>')

    # Property definitions (after elements and relationships per XSD sequence)
    if prop_names:
        lines.append('  <propertyDefinitions>')
        for pname in prop_names:
            pid = propdef_ids[pname]
            lines.append(f'    <propertyDefinition identifier="{pid}" type="string">')
            lines.append(f'      <name xml:lang="en">{_esc(pname)}</name>')
            lines.append('    </propertyDefinition>')
        lines.append('  </propertyDefinitions>')

    lines.append('</model>')
    lines.append('')

    output_path.write_text('\n'.join(lines), encoding='utf-8')


def _esc(text: str) -> str:
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ttl_to_archimate_xml.py <input.ttl> [output.xml]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        out_path = input_path.with_suffix(".xml")

    convert(input_path, out_path)
