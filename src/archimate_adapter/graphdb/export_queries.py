from textwrap import dedent

from archimate_adapter.namespaces import ARCHIMATE_NS, DCT_NS, OWL_NS, RDF_NS


def select_elements_query(graph_iri: str | None = None) -> str:
    graph_open = f"GRAPH <{graph_iri}> {{" if graph_iri else ""
    graph_close = "}" if graph_iri else ""

    return dedent(
        f"""
        PREFIX rdf: <{RDF_NS}>
        PREFIX owl: <{OWL_NS}>
        PREFIX archimate: <{ARCHIMATE_NS}>
        PREFIX dct: <{DCT_NS}>

        SELECT ?element ?type ?id ?name ?documentation ?junctionType
        WHERE {{
          {graph_open}
          ?element rdf:type ?type ;
                   archimate:identifier ?id .

          FILTER(?type != owl:NamedIndividual)

          OPTIONAL {{ ?element archimate:name ?name . }}
          OPTIONAL {{ ?element dct:description ?documentation . }}
          OPTIONAL {{ ?element archimate:junctionType ?junctionType . }}
          {graph_close}
        }}
        ORDER BY ?id
        """
    ).strip()


def select_relationships_query(
    predicate_iris: list[str],
    graph_iri: str | None = None,
) -> str:
    if not predicate_iris:
        raise ValueError("predicate_iris must not be empty")

    values = " ".join(f"<{predicate_iri}>" for predicate_iri in predicate_iris)
    graph_open = f"GRAPH <{graph_iri}> {{" if graph_iri else ""
    graph_close = "}" if graph_iri else ""

    return dedent(
        f"""
        PREFIX archimate: <{ARCHIMATE_NS}>
        PREFIX dct: <{DCT_NS}>

        SELECT ?src ?pred ?tgt ?rid ?rname ?rdocumentation
        WHERE {{
          VALUES ?pred {{ {values} }}

          {graph_open}
          ?src ?pred ?tgt .

          OPTIONAL {{
            << ?src ?pred ?tgt >> archimate:identifier ?rid .
          }}
          OPTIONAL {{
            << ?src ?pred ?tgt >> archimate:name ?rname .
          }}
          OPTIONAL {{
            << ?src ?pred ?tgt >> dct:description ?dctDoc .
          }}
          OPTIONAL {{
            << ?src ?pred ?tgt >> archimate:description ?archDoc .
          }}
          BIND(COALESCE(?dctDoc, ?archDoc) AS ?rdocumentation)
          {graph_close}
        }}
        ORDER BY ?rid ?src ?pred ?tgt
        """
    ).strip()