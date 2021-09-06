"""Write Gradoop file format and read Gradoop file format."""
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

INV_TYPES = {
    str: "string",
    int: "int",
    float: "float",
    bool: "boolean",
}

VertexLine = namedtuple("VertexLine", ["id", "graph_ids", "type", "props"])
EdgeLine = namedtuple(
    "EdgeLine", ["id", "graph_ids", "source_id", "target_id", "type", "props"]
)


def int_to_gradoop_id(value: int) -> str:
    """Casts to Gradoop id, which are 12 byte hexadecimal strings.

    Parameters
    ----------
    value : int
        Value to cast

    Returns
    -------
    str
        12 byte hexadecimal string (without leading '0x').
    """
    # see https://stackoverflow.com/a/12638477
    # first two characters are leading 0x
    return f"{value:#0{26}x}"[2:]


def is_gradoop_id(value) -> bool:
    """Check if value is a valid Gradoop id.

    Gradoop ids are 12 byte hexadecimal strings

    Parameters
    ----------
    value
        Value to check

    Returns
    -------
    bool
        True if is valid Gradoop id
    """
    if isinstance(value, str) and len(value) == 24:
        try:
            int(value, 16)
            return True
        except ValueError:
            return False
    return False


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
        if len(prop_name_type) == 1:
            continue
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
            e_props = _prop_creation("e", label, metadata, properties, is_edge=True)
            for g in _graph_containment(graphs):
                graph_edges[g][source][target][label] = e_props
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
    kgs: Dict[str, KG],
    label_attr: str = "_label",
    attribute_type_mapping: Dict = None,
    vertex_id_attr_name: str = None,
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
                if vertex_id_attr_name is not None:
                    v_metadata[cur_label][vertex_id_attr_name] = str
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
    kgs: Dict[str, KG],
    label_attr: str = "_label",
    attribute_type_mapping: Dict = None,
    vertex_id_attr_name: str = None,
    graph_name_as_property: str = None,
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
        kgs,
        label_attr=label_attr,
        attribute_type_mapping=vertex_type_mapping,
        vertex_id_attr_name=vertex_id_attr_name,
    )

    graph_metadata = {}
    for i, k in enumerate(kgs.values(), start=1):
        props = {} if graph_name_as_property is None else {graph_name_as_property: str}
        if k.name is None:
            graph_metadata[f"graph{i}"] = props
        else:
            graph_metadata[k.name] = props

    return _fix_metadata_order(
        {"g": graph_metadata, "e": edge_metadata, "v": vertex_metadata}
    )


def _create_vertex_lines(
    kgs: Dict[str, KG], label_attr: str, vertex_metadata: Dict, vertex_id_attr_name: str
):
    v_dict = {}
    vid_to_gid = {}
    for k_name, kg in kgs.items():
        for e_id, e_attr_dict in kg.entities.items():
            cur_label = e_attr_dict[label_attr]
            prop_line = []
            for attr_name, exp_type in zip(*vertex_metadata[cur_label]):
                if attr_name == vertex_id_attr_name:
                    attr_value = e_id
                else:
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
                if not is_gradoop_id(e_id):
                    grad_id = int_to_gradoop_id(len(v_dict))
                    vid_to_gid[e_id] = grad_id
                else:
                    grad_id = e_id
                v_dict[e_id] = VertexLine(grad_id, [k_name], cur_label, prop_string)
    return list(v_dict.values()), vid_to_gid


def _create_edge_lines(kgs: Dict[str, KG], edge_metadata: Dict, vid_to_gid: Dict):
    e_dict = {}
    for k_name, kg in kgs.items():
        for source_id, target_rel_dict in kg.rel.items():
            for target_id, rel_dict in target_rel_dict.items():
                if isinstance(rel_dict, str):
                    # in this case
                    # relation does not have attributes
                    # and simply has the relation name
                    # which we use as edge type for gradoop
                    rel_dict = {rel_dict: {}}
                for cur_label, prop_dict in rel_dict.items():
                    prop_line = []
                    for attr_name, exp_type in zip(*edge_metadata[cur_label]):
                        attr_value = prop_dict.get(attr_name, "")
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
                        edge_id = int_to_gradoop_id(len(e_dict))
                        if vid_to_gid is not None:
                            source_id = vid_to_gid.get(source_id, source_id)
                            target_id = vid_to_gid.get(target_id, target_id)
                        e_dict[tmp_id] = EdgeLine(
                            edge_id,
                            [k_name],
                            source_id,
                            target_id,
                            cur_label,
                            prop_string,
                        )
    return list(e_dict.values())


def _create_graph_lines(
    kgs: Dict[str, KG],
    graph_metadata: Dict,
    default_type="graph",
    graph_name_as_property: str = None,
):
    g_lines = []
    for g_id, kg in kgs.items():
        if kg.name is None:
            g_lines.append((g_id, default_type, ""))
        else:
            metadata = graph_metadata[kg.name]
            # TODO graphs cannot really have attributes yet
            props = []
            for m_att in metadata[0]:
                if (
                    graph_name_as_property is not None
                    and m_att == graph_name_as_property
                ):
                    props.append(kg.name)
                else:
                    props.append("")
            prop_string = "|".join(props)
            g_lines.append((g_id, kg.name, prop_string))
    return g_lines


def _create_metadata_lines(metadata):
    m_lines = []
    for ele_type, ele_dict in metadata.items():
        for inner_type, prop_list in ele_dict.items():
            props_list = []
            for prop_name, type_class in zip(*prop_list):
                if isinstance(type_class, str):
                    props_list.append(f"{prop_name}:{type_class}")
                else:
                    props_list.append(f"{prop_name}:{INV_TYPES[type_class]}")
            props = ",".join(props_list)
            m_lines.append((ele_type, inner_type, props))
    return m_lines


def _kgs_dict_to_gradoop_id(kgs: Dict) -> Dict:
    return {
        int_to_gradoop_id(i): kg_name_value[1]
        for i, kg_name_value in enumerate(kgs.items())
    }


def _write_lines(lines, out_path):
    with open(out_path, "w") as out_file:
        for line in lines:
            if isinstance(line, (VertexLine, EdgeLine)):
                line = list(line)
                line[1] = "[" + ",".join(line[1]) + "]"
            out_file.write(";".join([str(ele) for ele in line]) + "\n")


def write_to_csv_datasource(
    kgs: Union[KG, Dict[str, KG]],
    out_path: str,
    label_attr: str = "_label",
    attribute_type_mapping: Dict = None,
    vertex_id_attr_name: str = "_forayer_id",
    default_graph_type: str = "graph",
    graph_name_as_property: str = None,
    overwrite: bool = False,
):
    """Write knowledge graph(s) to Gradoop CSV Datasource.

    Parameters
    ----------
    kgs : Union[KG, Dict[str, KG]]
        Knowledge Graph(s) to serialize.
    out_path : str
        Folder where this data will be serialized to.
    label_attr : str, Default = "_label"
        Vertex attribute to use for Gradoop's special type attribute.
    attribute_type_mapping : Dict, Default=None
        Manually set attribute types.
    vertex_id_attr_name : str, Default="_forayer_id"
        Save the current entity id as property with this name.
        If set to None, entity id is not saved.
    default_graph_type : str
        Label graphs as this type if they do not have a name.
    graph_name_as_property : str
        Save the name of graphs as seperate property.
    overwrite : bool
        If True, overwrites existing files at output.
    """
    if os.path.exists(out_path) and not overwrite:
        raise ValueError(f"Path {out_path} already exists")
    os.makedirs(out_path, exist_ok=True)
    graphs_csv_path = os.path.join(out_path, "graphs.csv")
    vertices_csv_path = os.path.join(out_path, "vertices.csv")
    edges_csv_path = os.path.join(out_path, "edges.csv")
    metadata_csv_path = os.path.join(out_path, "metadata.csv")
    metadata = _create_metadata(
        kgs=kgs,
        label_attr=label_attr,
        attribute_type_mapping=attribute_type_mapping,
        vertex_id_attr_name=vertex_id_attr_name,
        graph_name_as_property=graph_name_as_property,
    )
    kg_dict_with_gid = _kgs_dict_to_gradoop_id(kgs)
    vertex_lines, vid_to_gid = _create_vertex_lines(
        kgs=kg_dict_with_gid,
        label_attr=label_attr,
        vertex_metadata=metadata["v"],
        vertex_id_attr_name=vertex_id_attr_name,
    )

    edge_lines = _create_edge_lines(
        kgs=kg_dict_with_gid, edge_metadata=metadata["e"], vid_to_gid=vid_to_gid
    )
    graph_lines = _create_graph_lines(
        kgs=kg_dict_with_gid,
        graph_metadata=metadata["g"],
        default_type=default_graph_type,
        graph_name_as_property=graph_name_as_property,
    )
    metadata_lines = _create_metadata_lines(metadata)
    _write_lines(graph_lines, graphs_csv_path)
    _write_lines(edge_lines, edges_csv_path)
    _write_lines(vertex_lines, vertices_csv_path)
    _write_lines(metadata_lines, metadata_csv_path)
