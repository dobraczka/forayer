"""Read and write semantic web sources."""
import logging
from collections import defaultdict
from typing import Callable

from forayer.knowledge_graph import KG
from rdflib import Graph
from rdflib.term import Literal
from tqdm import tqdm


def cast_to_python_type(lit):
    return lit.toPython()


def add_multi_value(prev, new):
    if not isinstance(prev, set):
        prev = {prev}
    prev.add(new)
    return prev


def load_from_triples(
    in_path: str,
    literal_cleaning_func: Callable = None,
    format: str = None,
    kg_name: str = None,
    multi_value: Callable = None,
) -> KG:
    """Create knowledge graph object.

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
    logging.info(f"Reading graph from {in_path}")
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
