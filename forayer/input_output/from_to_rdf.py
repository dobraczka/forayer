"""Read and write semantic web sources."""
import logging
from collections import defaultdict
from typing import Callable, Set

import rdflib
from forayer.knowledge_graph import KG
from rdflib import Graph
from rdflib.term import Literal
from tqdm import tqdm


def load_from_rdf(
    in_path: str,
    literal_cleaning_func: Callable = None,
    format: str = None,
    kg_name: str = None,
    multi_value: Callable = None,
) -> KG:
    """Create knowledge graph object from rdf source.

    Parameters
    ----------
    in_path : str
        Path of triple file.
    literal_cleaning_func: Callable
        Function to preprocess literals,
        if None will simply cast to python types.
    format : str
        Triple format ("xml”, “n3” (use for turtle), “nt” or “trix”).
    kg_name : str
        How to name the knowledge graph object.
    multi_value : Callable
        How to handle multiple attribute values for an
        entity, attribute name combination.
        Default creates a set and adds to it

    Returns
    -------
    KG
        the loaded kg object
    """
    if literal_cleaning_func is None:
        literal_cleaning_func = cast_to_python_type
    if multi_value is None:
        multi_value = add_multi_value
    g = Graph()
    logging.info(f"Reading graph from {in_path}. This might take a while...")
    g.parse(in_path, format=format)
    entities = defaultdict(dict)
    rel = defaultdict(dict)
    for stmt in tqdm(g, desc="Transforming graph", total=len(g)):
        s, p, o = stmt
        if isinstance(o, Literal):
            value = literal_cleaning_func(o)
            if str(p) in entities[str(s)]:
                value = multi_value(entities[str(s)][str(p)], value)
            entities[str(s)][str(p)] = value
        else:
            rel[str(s)][str(o)] = str(p)
    return KG(entities=entities, rel=rel, name=kg_name)


def write_to_rdf(
    kg: KG, out_path: str, format: str, prefix: str = "", attr_mapping: dict = None
):
    """Write the forayer knowledge graph to a rdf serialization format.

    Parameters
    ----------
    kg : KG
        The knowledge graph that will be serialized.
    out_path : str
        The path where it should be serialized to.
    format : str
        The desired rdf format.
    prefix : str
        Prefix for the entities in the graph.
    attr_mapping : dict
       Mapping of attribute names.
    """
    kg.to_rdflib(prefix=prefix, attr_mapping=attr_mapping).serialize(
        destination=out_path, format=format
    )


def cast_to_python_type(lit: rdflib.term.Literal):
    """Casts a literal to the respective python type.

    Parameters
    ----------
    lit : rdflib.term.Literal
       The literal that is to be cast.

    Returns
    -------
    Any
        The literal as the respective python object
    """
    if lit.datatype is not None and "langString" in lit.datatype:
        # lang strings are not automatically cast
        return str(lit)
    return lit.toPython()


def add_multi_value(prev, new) -> Set:
    """Add a  value to a set or create a new set with prev and new.

    Parameters
    ----------
    prev
        Existing value.
    new
        New value, that should be added.

    Returns
    -------
    Set
        Set containing the previous and new elements.
    """
    if not isinstance(prev, set):
        prev = {prev}
    prev.add(new)
    return prev
