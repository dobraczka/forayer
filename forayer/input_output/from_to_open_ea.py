"""IO module for OpenEA data."""
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from forayer import forayer_stow
from forayer.knowledge_graph import KG, ClusterHelper, ERTask


def _get_cleaned_split(line: str, delimiter: str):
    seperated = line.split(delimiter)
    seperated[-1] = seperated[-1].strip()
    return seperated


def read_attr_triples(
    path: str, delimiter="\t", url: Optional[str] = None, encoding="utf-8"
) -> Dict[str, Dict[str, Any]]:
    """Read attribute triples from csv into a dictionary.

    This functions returns the triples as dictionary, where entity ids are
    keys and the values are attribute dictionaries, with the attribute name
    as key.

    Parameters
    ----------
    path: str
        Path to the file
        If remote: path to the file inside the archive
    delimiter: str, default = tab
        Delimiter of the csv file
    url: Optional[str]
        Url to remote zip archive where file is
    encoding: str, default utf-8
        specific encoding to use

    Returns
    -------
    ent_attr_dict: Dict[str, Dict[str, Any]]
        Entity and attribute dictionary

    """
    ent_attr_dict: Dict[str, Dict[str, Any]] = defaultdict(dict)
    if url:
        context = forayer_stow.ensure_open_zip(url=url, inner_path=path)
    else:
        context = open(path, "r")  # noqa: SIM115
    with context as in_file:
        for line in in_file:
            if isinstance(line, bytes):
                line = line.decode(encoding)
            e_id, prop, value = _get_cleaned_split(line, delimiter)
            if e_id in ent_attr_dict and prop in ent_attr_dict[e_id]:
                # multi-value case
                if isinstance(ent_attr_dict[e_id][prop], set):
                    ent_attr_dict[e_id][prop].add(value)
                else:
                    ent_attr_dict[e_id][prop] = {ent_attr_dict[e_id][prop], value}
            else:
                ent_attr_dict[e_id][prop] = value
    return ent_attr_dict


def read_rel_triples(
    path: str, delimiter="\t", url: Optional[str] = None, encoding="utf-8"
) -> Dict[str, Dict[str, Any]]:
    """Read relation triples.

    This functions returns the triples as dictionary. Containing
    the relations from left to right,i.e.  given a triple (s,p,o)
    the dictionary would be {s: {o: p}}

    Parameters
    ----------
    path: str
        Path to the file
        If remote: path to the file inside the archive
    delimiter: str, default = tab
        Delimiter of the csv file
    url: Optional[str]
        Url to remote zip archive where file is
    encoding: str, default utf-8
        specific encoding to use

    Returns
    -------
    rel_dict: Dict[str, Dict[str, Any]]
        Dictionary containing relation triples with subjects as key
        of outer dict
    """
    rel_dict: Dict[str, Dict[str, Any]] = defaultdict(dict)
    if url:
        context = forayer_stow.ensure_open_zip(url=url, inner_path=path)
    else:
        context = open(path, "r")  # noqa: SIM115
    with context as in_file:
        for line in in_file:
            if isinstance(line, bytes):
                line = line.decode(encoding)
            left_id, rel, right_id = _get_cleaned_split(line, delimiter)

            if left_id in rel_dict and right_id in rel_dict[left_id]:
                # multi-value case
                if isinstance(rel_dict[left_id][right_id], set):
                    rel_dict[left_id][right_id].add(rel)
                else:
                    rel_dict[left_id][right_id] = {rel_dict[left_id][right_id], rel}
            else:
                rel_dict[left_id][right_id] = rel
    return rel_dict


def read_links(
    path: str, delimiter="\t", url: Optional[str] = None, encoding="utf-8"
) -> ClusterHelper:
    """Read entity links.

    Parameters
    ----------
    path: str
        Path to the file
        If remote: path to the file inside the archive
    delimiter: str, default = tab
        Delimiter of the csv file
    url: Optional[str]
        Url to remote zip archive where file is
    encoding: str, default utf-8
        specific encoding to use

    Returns
    -------
    ClusterHelper
        ClusterHelper instance containing all links

    """
    if url:
        context = forayer_stow.ensure_open_zip(url=url, inner_path=path)
    else:
        context = open(path, "r")  # noqa: SIM115
    with context as in_file:
        links = {}
        for line in in_file:
            if isinstance(line, bytes):
                line = line.decode(encoding)
            left, right = _get_cleaned_split(line, delimiter)
            links[left] = right
    return ClusterHelper(links)


def _get_kg_name_from_path(path: str):
    if "D_W" in path:
        return "DBpedia", "Wikidata"
    if "D_Y" in path:
        return "DBpedia", "Yago"
    if "EN_DE" in path:
        return "English-DBpedia", "German-DBpedia"
    if "EN_FR" in path:
        return "English-DBpedia", "French-DBpedia"
    raise ValueError(
        "Unknown knowledge graph names, please specifiy explicitly in from_openea via"
        " kg_names parameter"
    )


def create_kg(path: str, one_or_two: str, name: str, url: Optional[str] = None) -> KG:
    """Create a KG object from open ea files given in path.

    Parameters
    ----------
    path : str
        path to open ea files of dataset pair
    one_or_two : str
        which KG to create (either "1" or "2")
    name : str
        name of KG
    url : str
        url to remote archive if the files are remote

    Returns
    -------
    KG
        knowledge graph object
    """
    attr_trip_path = os.path.join(path, f"attr_triples_{one_or_two}")
    rel_trip_path = os.path.join(path, f"rel_triples_{one_or_two}")
    attr_trip = read_attr_triples(path=attr_trip_path, url=url)
    rel_trip = read_rel_triples(path=rel_trip_path, url=url)
    return KG(attr_trip, rel_trip, name)


def from_openea(
    path: str, kg_names: Optional[Tuple[str, str]] = None, url: Optional[str] = None
) -> ERTask:
    """Create ERTask object from open ea-style files.

    Parameters
    ----------
    path : str
        path to openea files of dataset pair
        for remote files, the root folder in the zip
    kg_names: Optional[Tuple[str,str]]
        optionally set knowledge graph names explicitly
    url: Optional[str]
        url to remote archive if the files are remote

    Returns
    -------
    ERTask
        er_task object
    """
    if not kg_names:
        kg_names = _get_kg_name_from_path(path)

    kg1 = create_kg(path, "1", kg_names[0], url=url)
    kg2 = create_kg(path, "2", kg_names[1], url=url)
    link_path = os.path.join(path, "ent_links")
    clusters = read_links(path=link_path, url=url)
    return ERTask(kgs=[kg1, kg2], clusters=clusters)
