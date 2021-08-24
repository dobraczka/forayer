import csv
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from forayer.knowledge_graph import KG
from forayer.utils.dict_help import nested_ddict, nested_ddict2dict

TYPE_CONVERSION = {
    "string": str,
    "long": int,
    "int": int,
    "float": float,
    "double": float,
    "boolean": lambda x: x == "true",
}


def _load_metadata(path: str) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
    metadata = {"g": defaultdict(list), "v": defaultdict(list), "e": defaultdict(list)}

    with open(path, "r") as in_file:
        reader = csv.reader(in_file, delimiter=";")
        for row in reader:
            if len(row) == 2:
                gve, label = row
                properties = []
            else:
                gve, label, keys = row
                properties = [tuple(p.split(":")) for p in keys.split(",")]
            if gve not in ["g", "v", "e"]:
                raise ValueError(
                    f"Unknown node type specifier '{gve}', only 'g','v' or 'e' allowed"
                )
            metadata[gve][label] = properties
    # cast to normal dict
    return {
        "g": dict(metadata["g"]),
        "v": dict(metadata["v"]),
        "e": dict(metadata["e"]),
    }


def _prop_creation(element_type, label, metadata, properties):
    props = {"_label": label}
    for prop_name_type, prop_value in zip(
        metadata[element_type][label], properties.split("|")
    ):
        prop_name, prop_type = prop_name_type
        if prop_value != "":
            props[prop_name] = TYPE_CONVERSION[prop_type](prop_value)
    return props


def _load_graphs(path: str, metadata: Dict[str, Dict[str, List[Tuple[str, str]]]]):
    graphs = {}
    with open(path, "r") as in_file:
        reader = csv.reader(in_file, delimiter=";")
        for row in reader:
            g_id, label, properties = row
            graphs[g_id] = _prop_creation("g", label, metadata, properties)
    return graphs


def _graph_containment(graphs: str):
    return graphs[1:-1].split(",")


def _load_vertices(path: str, metadata: Dict[str, Dict[str, List[Tuple[str, str]]]]):
    graph_vertices = nested_ddict()
    with open(path, "r") as in_file:
        reader = csv.reader(in_file, delimiter=";")
        for row in reader:
            v_id, graphs, label, properties = row
            v_props = _prop_creation("v", label, metadata, properties)
            for g in _graph_containment(graphs):
                graph_vertices[g][v_id] = v_props
    return nested_ddict2dict(graph_vertices)


def _load_edges(path: str, metadata: Dict[str, Dict[str, List[Tuple[str, str]]]]):
    graph_edges = nested_ddict()
    with open(path, "r") as in_file:
        reader = csv.reader(in_file, delimiter=";")
        for row in reader:
            e_id, graphs, source, target, label, properties = row
            e_props = _prop_creation("e", label, metadata, properties)
            for g in _graph_containment(graphs):
                graph_edges[g][source][target] = e_props
    return nested_ddict2dict(graph_edges)


def load_from_csv_datasource(folder_path: str, graph_name_property: str = None):
    graphs_csv_path = os.path.join(folder_path, "graphs.csv")
    vertices_csv_path = os.path.join(folder_path, "vertices.csv")
    edges_csv_path = os.path.join(folder_path, "edges.csv")
    metadata_csv_path = os.path.join(folder_path, "metadata.csv")

    metadata = _load_metadata(metadata_csv_path)
    graphs = _load_graphs(graphs_csv_path, metadata)
    vertices = _load_vertices(vertices_csv_path, metadata)
    edges = _load_edges(edges_csv_path, metadata)
    if graph_name_property is not None:
        return {
            g: KG(
                entities=vertices[g],
                rel=edges[g],
                name=graphs[g][graph_name_property],
            )
            for g in graphs.keys()
        }
    else:
        return {
            g: KG(entities=vertices[g], rel=edges[g], name=g) for g in graphs.keys()
        }
