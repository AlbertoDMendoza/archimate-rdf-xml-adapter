"""
Convert a Mendoza-style ArchiMate TTL file to ArchiMate Exchange XML.

Maps Mendoza specialization types (python:PythonClass, laravel:LaravelFolder, etc.)
to the closest standard ArchiMate element types so the output is valid Exchange XML.

Preserves the original Mendoza type and all specialization datatype properties
as ArchiMate Exchange propertyDefinitions / properties.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import rdflib
from rdflib import RDF, RDFS, Namespace

ARCHIMATE = Namespace("https://purl.org/archimate#")
PYTHON = Namespace("https://purl.org/archimate/python#")
LARAVEL = Namespace("https://purl.org/archimate/laravel#")
DCT = Namespace("http://purl.org/dc/terms/")

# Map RDF types to ArchiMate Exchange XML xsi:type values
TYPE_MAP = {
    str(ARCHIMATE.SystemSoftware): "SystemSoftware",
    str(ARCHIMATE.ApplicationComponent): "ApplicationComponent",
    str(ARCHIMATE.ApplicationFunction): "ApplicationFunction",
    str(ARCHIMATE.DataObject): "DataObject",
    str(ARCHIMATE.Node): "Node",
    str(LARAVEL.LaravelApplication): "ApplicationComponent",
    str(LARAVEL.LaravelFolder): "Grouping",
    str(LARAVEL.LaravelSourceFile): "DataObject",
    str(PYTHON.PythonClass): "DataObject",
    str(PYTHON.PythonFunction): "ApplicationFunction",
    str(PYTHON.PythonModule): "ApplicationComponent",
    str(PYTHON.PythonPackage): "ApplicationComponent",
}

# Map RDF predicates to ArchiMate Exchange XML relationship xsi:type values
REL_MAP = {
    str(ARCHIMATE.composition): "Composition",
    str(ARCHIMATE.realization): "Realization",
    str(ARCHIMATE.serving): "Serving",
    str(ARCHIMATE.access): "Access",
    str(ARCHIMATE.aggregation): "Aggregation",
    str(ARCHIMATE.assignment): "Assignment",
    str(ARCHIMATE.association): "Association",
    str(ARCHIMATE.flow): "Flow",
    str(ARCHIMATE.influence): "Influence",
    str(ARCHIMATE.specialization): "Specialization",
    str(ARCHIMATE.triggering): "Triggering",
    str(PYTHON.moduleContainsClass): "Composition",
    str(PYTHON.moduleContainsFunction): "Composition",
    str(PYTHON.moduleImports): "Serving",
    str(PYTHON.classExtends): "Specialization",
}

# Specialization datatype properties to capture as Exchange XML properties
SPEC_PROPERTIES = {
    str(PYTHON.className): "python:className",
    str(PYTHON.classModule): "python:classModule",
    str(PYTHON.classBase): "python:classBase",
    str(PYTHON.functionName): "python:functionName",
    str(PYTHON.functionModule): "python:functionModule",
    str(PYTHON.functionDecorator): "python:functionDecorator",
    str(PYTHON.moduleName): "python:moduleName",
    str(PYTHON.packageName): "python:packageName",
    str(PYTHON.packageVersion): "python:packageVersion",
    str(LARAVEL.filePath): "laravel:filePath",
    str(LARAVEL.folderPath): "laravel:folderPath",
}


@dataclass
class ElementInfo:
    identifier: str
    xml_type: str
    name: str | None = None
    documentation: str | None = None
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class RelInfo:
    identifier: str
    xml_type: str
    source_id: str
    target_id: str


def convert(ttl_path: str | Path, output_path: str | Path) -> None:
    g = rdflib.Graph()
    g.parse(str(ttl_path), format="turtle")

    # Collect all subjects that have an archimate:identifier
    id_map: dict[str, str] = {}  # URI -> archimate:identifier
    for s, _p, o in g.triples((None, ARCHIMATE.identifier, None)):
        id_map[str(s)] = str(o)

    # Build elements with specialization properties
    elements: dict[str, ElementInfo] = {}
    for uri, arch_id in id_map.items():
        uri_ref = rdflib.URIRef(uri)

        # Determine ArchiMate XML type
        xml_type = None
        original_type = None
        for _s, _p, type_obj in g.triples((uri_ref, RDF.type, None)):
            type_str = str(type_obj)
            if type_str in TYPE_MAP:
                xml_type = TYPE_MAP[type_str]
                original_type = type_str
                break

        if xml_type is None:
            continue

        # Get name
        name = None
        for _s, _p, name_obj in g.triples((uri_ref, ARCHIMATE["name"], None)):
            name = str(name_obj)
            break

        # Get documentation
        doc = None
        for _s, _p, doc_obj in g.triples((uri_ref, DCT.description, None)):
            doc = str(doc_obj)
            break

        # Collect specialization properties
        props: dict[str, str] = {}

        # Always store original Mendoza type as a property
        if original_type:
            # Use the short form: e.g. "python:PythonClass"
            short_type = original_type
            for prefix, ns in [("archimate:", str(ARCHIMATE)),
                               ("python:", str(PYTHON)),
                               ("laravel:", str(LARAVEL))]:
                if original_type.startswith(ns):
                    short_type = prefix + original_type[len(ns):]
                    break
            props["Specialization"] = short_type

        # Collect all known specialization datatype properties
        for pred_uri, prop_name in SPEC_PROPERTIES.items():
            pred = rdflib.URIRef(pred_uri)
            for _s, _p, val in g.triples((uri_ref, pred, None)):
                if isinstance(val, rdflib.Literal):
                    props[prop_name] = str(val)
                break

        elements[uri] = ElementInfo(
            identifier=arch_id,
            xml_type=xml_type,
            name=name,
            documentation=doc,
            properties=props,
        )

    # Build relationships
    relationships: list[RelInfo] = []
    rel_counter = 0
    for pred_str, rel_type in REL_MAP.items():
        pred = rdflib.URIRef(pred_str)
        for s, _p, o in g.triples((None, pred, None)):
            s_uri = str(s)
            o_uri = str(o)
            if s_uri in elements and o_uri in elements:
                rel_counter += 1
                relationships.append(RelInfo(
                    identifier=f"rel-{rel_counter:04d}",
                    xml_type=rel_type,
                    source_id=elements[s_uri].identifier,
                    target_id=elements[o_uri].identifier,
                ))

    # Collect all property names used across elements for propertyDefinitions
    all_prop_names: list[str] = []
    seen: set[str] = set()
    sorted_elements = sorted(elements.values(), key=lambda e: e.identifier)
    for elem in sorted_elements:
        for pname in elem.properties:
            if pname not in seen:
                seen.add(pname)
                all_prop_names.append(pname)
    all_prop_names.sort()

    # Assign stable identifiers to property definitions
    propdef_ids: dict[str, str] = {}
    for i, pname in enumerate(all_prop_names, start=1):
        propdef_ids[pname] = f"propdef-{i:03d}"

    # Write XML
    model_name = Path(ttl_path).stem
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_xml(sorted_elements, relationships, propdef_ids, all_prop_names,
               output, model_name)

    print(f"Converted: {len(sorted_elements)} elements, {len(relationships)} relationships")
    print(f"Property definitions: {len(all_prop_names)}")
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

    # Property definitions (must come after elements and relationships per XSD sequence)
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
