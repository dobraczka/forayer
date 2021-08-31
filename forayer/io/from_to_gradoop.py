import csv
import os
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple, Union

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

VertexLine = namedtuple("VertexLine", ["id", "graph_ids", "type", "props"])
EdgeLine = namedtuple(
    "EdgeLine", ["id", "graph_ids", "source_id", "target_id", "type", "props"]
)


def _int_to_gradoop_id(value: int):
    """Gradoop ids are 12 byte hexadecimal strings."""
    # see https://stackoverflow.com/a/12638477
    # first two characters are leading 0x
    return f"{value:#0{26}x}"[2:]


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


def _prop_creation(element_type, label, metadata, properties, is_edge=False):
    props = {} if is_edge else {"_label": label}
    for prop_name_type, prop_value in zip(
        metadata[element_type][label], properties.split("|")
    ):
        prop_name, prop_type = prop_name_type
        if prop_value != "":
            props[prop_name] = TYPE_CONVERSION[prop_type](prop_value)
    if is_edge:
        return {label: props}
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


def load_from_csv_datasource(
    folder_path: str, graph_name_property: str = None
) -> Dict[str, KG]:
    """Load Gradoop graph from csv datasource.

    Parameters
    ----------
    folder_path : str
        Path for folder that contains graph.
    graph_name_property : str
        Name of graph property that will be used to name graphs.
        If None use graph id.

    Returns
    -------
    Dict[str,KG]
        Dictionary of knowledge graphs.
    """
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


def _gather_edge_metadata(kgs: Dict[str, KG], attribute_type_mapping: Dict = None):
    e_metadata = nested_ddict()
    for kg in kgs.values():
        for _, rel_dict in kg.rel.items():
            for _, rel_prop_dict in rel_dict.items():
                if isinstance(rel_prop_dict, str):
                    # in this case
                    # relation does not have attributes
                    # and simply has the relation name
                    # which we use as edge type for gradoop
                    e_metadata[rel_prop_dict] = {}
                    continue
                for e_type, inner_prop_dict in rel_prop_dict.items():
                    for e_prop_name, e_prop_value in inner_prop_dict.items():
                        if (
                            attribute_type_mapping is not None
                            and e_type in attribute_type_mapping
                            and e_prop_name in attribute_type_mapping[e_type]
                        ):
                            e_metadata[e_type][e_prop_name] = attribute_type_mapping[
                                e_type
                            ][e_prop_name]
                        elif e_metadata[e_type][e_prop_name] != {} and e_metadata[
                            e_type
                        ][e_prop_name] != type(e_prop_value):
                            raise ValueError(
                                f"Inconsistent typing for {e_prop_name} in relation"
                                f" type {e_type}"
                            )
                        else:
                            e_metadata[e_type][e_prop_name] = type(e_prop_value)
    return nested_ddict2dict(e_metadata)


def _gather_vertex_metadata(
    kgs: Dict[str, KG], label_attr: str = "_label", attribute_type_mapping: Dict = None
):
    v_metadata = nested_ddict()
    for kg in kgs.values():
        for e_id, e_attr_dict in kg.entities.items():
            if label_attr not in e_attr_dict:
                raise ValueError(
                    f"Entity {e_id} does not contain the required label attribute"
                    f" '{label_attr}'"
                )
            else:
                cur_label = e_attr_dict[label_attr]
            for attr_name, attr_val in e_attr_dict.items():
                if attr_name == label_attr:
                    continue
                elif (
                    attribute_type_mapping is not None
                    and cur_label in attribute_type_mapping
                    and attr_name in attribute_type_mapping[cur_label]
                ):
                    v_metadata[cur_label][attr_name] = attribute_type_mapping[
                        cur_label
                    ][attr_name]
                elif v_metadata[cur_label][attr_name] != {} and v_metadata[cur_label][
                    attr_name
                ] != type(attr_val):
                    raise ValueError(
                        f"Inconsistent typing for {attr_name} in Entity type"
                        f" {cur_label}"
                    )
                else:
                    v_metadata[cur_label][attr_name] = type(attr_val)
    return nested_ddict2dict(v_metadata)


def _fix_metadata_order(metadata: Dict):
    fixed_metadata = {}
    for element_type, ele_meta in metadata.items():
        v_out = {}
        for inner_type, attr_dict in ele_meta.items():
            inner_list = [[], []]  # name, type
            for a_name, a_type in attr_dict.items():
                inner_list[0].append(a_name)
                inner_list[1].append(a_type)
            v_out[inner_type] = inner_list
        fixed_metadata[element_type] = v_out
    return fixed_metadata


def _create_metadata(
    kgs: Dict[str, KG], label_attr: str = "_label", attribute_type_mapping: Dict = None
):
    edge_type_mapping = None
    vertex_type_mapping = None
    if attribute_type_mapping is not None:
        edge_type_mapping = (
            None if "e" not in attribute_type_mapping else attribute_type_mapping["e"]
        )
        vertex_type_mapping = (
            None if "v" not in attribute_type_mapping else attribute_type_mapping["v"]
        )
    edge_metadata = _gather_edge_metadata(kgs, attribute_type_mapping=edge_type_mapping)

    vertex_metadata = _gather_vertex_metadata(
        kgs, label_attr=label_attr, attribute_type_mapping=vertex_type_mapping
    )

    graph_metadata = {}
    for i, k in enumerate(kgs.values(), start=1):
        if k.name is None:
            graph_metadata[f"graph{i}"] = {}
        else:
            graph_metadata[k.name] = {}

    return _fix_metadata_order(
        {"g": graph_metadata, "e": edge_metadata, "v": vertex_metadata}
    )


def _create_vertex_lines(kgs: Dict[str, KG], label_attr: str, vertex_metadata: Dict):
    v_dict = {}
    for k_name, kg in kgs.items():
        for e_id, e_attr_dict in kg.entities.items():
            cur_label = e_attr_dict[label_attr]
            prop_line = []
            for attr_name, exp_type in zip(*vertex_metadata[cur_label]):
                attr_value = e_attr_dict.get(attr_name, "")
                if attr_value != "":
                    if exp_type == bool:
                        attr_value = "true" if attr_value else "false"
                    elif not isinstance(exp_type, str):  # custom type
                        attr_value = exp_type(attr_value)
                prop_line.append(str(attr_value))
            prop_string = "|".join(prop_line)
            if e_id in v_dict:
                if v_dict[e_id].props != prop_string:
                    raise ValueError(
                        f"Entity {e_id} has inconsistent representation across"
                        f" graphs:{prop_string}\n and\n {v_dict[e_id][3]}"
                    )
                else:
                    v_dict[e_id].graph_ids.append(k_name)
            else:
                v_dict[e_id] = VertexLine(e_id, [k_name], cur_label, prop_string)
    return list(v_dict.values())


def _create_edge_lines(kgs: Dict[str, KG], edge_metadata: Dict):
    e_dict = {}
    for k_name, kg in kgs.items():
        for source_id, target_rel_dict in kg.rel.items():
            for target_id, rel_dict in target_rel_dict.items():
                prop_line = []
                if isinstance(rel_dict, str):
                    # in this case
                    # relation does not have attributes
                    # and simply has the relation name
                    # which we use as edge type for gradoop
                    cur_label = rel_dict
                else:
                    cur_label = list(rel_dict.keys())[0]
                    for attr_name, exp_type in zip(*edge_metadata[cur_label]):
                        attr_value = rel_dict[cur_label].get(attr_name, "")
                        if attr_value != "":
                            if exp_type == bool:
                                attr_value = "true" if attr_value else "false"
                            elif not isinstance(exp_type, str):  # custom type
                                attr_value = exp_type(attr_value)
                        prop_line.append(str(attr_value))
                tmp_id = str(source_id) + str(target_id) + str(cur_label)
                prop_string = "|".join(prop_line)
                if tmp_id in e_dict:
                    e_dict[tmp_id].graph_ids.append(k_name)
                else:
                    edge_id = _int_to_gradoop_id(len(e_dict))
                    e_dict[tmp_id] = EdgeLine(
                        edge_id, [k_name], source_id, target_id, cur_label, prop_string
                    )
    return list(e_dict.values())


def write_to_csv_datasource(
    kgs: Union[KG, Dict[str, KG]], out_path: str, attribute_type_mapping: Dict = None
):
    graphs_csv_path = os.path.join(out_path, "graphs.csv")
    vertices_csv_path = os.path.join(out_path, "vertices.csv")
    edges_csv_path = os.path.join(out_path, "edges.csv")
    metadata_csv_path = os.path.join(out_path, "metadata.csv")
    metadata = _create_metadata(kgs, attribute_type_mapping)
