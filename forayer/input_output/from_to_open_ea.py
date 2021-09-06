"""IO module for OpenEA data."""
import os
from collections import defaultdict
from typing import Dict

from forayer.knowledge_graph import KG, ClusterHelper, ERTask


def _get_cleaned_split(line: str, delimiter: str):
    seperated = line.split(delimiter)
    seperated[-1] = seperated[-1].strip()
    return seperated


def read_attr_triples(path: str, delimiter="\t") -> Dict[str, Dict[str, str]]:
    """Read attribute triples from csv into a dictionary.

    This functions returns the triples as dictionary, where entity ids are
    keys and the values are attribute dictionaries, with the attribute name
    as key.

    Parameters
    ----------
    path : str
        Path to the file
    delimiter: str, default = tab
        Delimiter of the csv file

    Returns
    -------
    ent_attr_dict: Dict[str, Dict[str, str]]
        Entity and attribute dictionary

    """
    ent_attr_dict = defaultdict(dict)
    with open(path, "r") as in_file:
        for line in in_file:
            e_id, prop, value = _get_cleaned_split(line, delimiter)
            ent_attr_dict[e_id][prop] = value
    return ent_attr_dict


def read_rel_triples(path: str, delimiter="\t") -> Dict[str, Dict[str, str]]:
    """Read relation triples.

    This functions returns the triples as dictionary. Containing
    the relations from left to right,i.e.  given a triple (s,p,o)
    the dictionary would be {s: {o: p}}

    Parameters
    ----------
    path : str
        Path to the file
    delimiter: str, default = tab
        Delimiter of the csv file

    Returns
    -------
    left_to_right: Dict[str, Dict[str, str]]
        Dictionary containing relation triples with subjects as key
        of outer dict
    """
    rel_dict = defaultdict(dict)
    with open(path, "r") as in_file:
        for line in in_file:
            left_id, rel, right_id = _get_cleaned_split(line, delimiter)
            rel_dict[left_id][right_id] = rel
    return rel_dict


def _read_two_column(path, delimiter="\t") -> ClusterHelper:
    links = {}
    with open(path, "r") as infile:
        for line in infile:
            left, right = _get_cleaned_split(line, delimiter)
            links[left] = right
    return ClusterHelper(links)


def read_links(path: str) -> ClusterHelper:
    """Read entity links.

    Parameters
    ----------
    path : str
        inpath

    Returns
    -------
    ClusterHelper
        ClusterHelper instance containing all links

    """
    return _read_two_column(path)


def _get_kg_name_from_path(path: str):
    if "D_W" in path:
        return "DBpedia", "Wikidata"
    if "D_Y" in path:
        return "DBpedia", "Yago"
    if "EN_DE" in path:
        return "English-DBpedia", "German-DBpedia"
    if "EN_FR" in path:
        return "English-DBpedia", "French-DBpedia"


def create_kg(path: str, one_or_two: str, name: str) -> KG:
    """Create a KG object from open ea files given in path.

    Parameters
    ----------
    path : str
        path to open ea files of dataset pair
    one_or_two : str
        which KG to create (either "1" or "2")
    name : str
        name of KG

    Returns
    -------
    KG
        knowledge graph object
    """
    attr_trip = read_attr_triples(os.path.join(path, f"attr_triples_{one_or_two}"))
    rel_trip = read_rel_triples(os.path.join(path, f"rel_triples_{one_or_two}"))
    return KG(attr_trip, rel_trip, name)


def from_openea(path: str) -> ERTask:
    """Create ERTask object from open ea files.

    Parameters
    ----------
    path : str
        path to openea files of dataset pair

    Returns
    -------
    ERTask
        er_task object
    """
    kg_names = _get_kg_name_from_path(path)
    kg1 = create_kg(path, "1", kg_names[0])
    kg2 = create_kg(path, "2", kg_names[1])
    return ERTask(kgs=[kg1, kg2], clusters=read_links(os.path.join(path, "ent_links")))
