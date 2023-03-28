import os
import pathlib

import pytest

from forayer.input_output.from_to_gradoop import (
    EdgeLine,
    VertexLine,
    _create_edge_lines,
    _create_graph_lines,
    _create_metadata,
    _create_metadata_lines,
    _create_vertex_lines,
    _kgs_dict_to_gradoop_id,
    is_gradoop_id,
    load_from_csv_datasource,
    write_to_csv_datasource,
)
from forayer.knowledge_graph import KG


@pytest.fixture
def gradoopy_kg():
    entities = {
        "000000000000000000000000": {"_label": "A", "a": "foo", "b": 42, "c": 13.37},
        "000000000000000000000001": {"_label": "A", "a": "bar", "b": 23, "c": 19.84},
        "000000000000000000000002": {"_label": "B", "a": 1234, "b": True, "c": 0.123},
        "000000000000000000000003": {"_label": "B", "a": 5678, "b": False, "c": 4.123},
        "000000000000000000000004": {"_label": "B", "a": 2342, "c": 19.84},
    }
    rel_1 = {
        "000000000000000000000002": {"000000000000000000000003": {"b": {"a": 2718}}},
    }
    rel_2 = {
        "000000000000000000000000": {
            "000000000000000000000001": {"a": {"a": 1234, "b": 13.37}}
        },
        "000000000000000000000001": {
            "000000000000000000000000": {"a": {"a": 5678, "b": 23.42}},
            "000000000000000000000002": {"b": {"a": 3141}},
        },
        "000000000000000000000002": {"000000000000000000000003": {"b": {"a": 2718}}},
        "000000000000000000000004": {
            "000000000000000000000000": {"a": {"b": 19.84}, "b": {}},
        },
    }
    expected_kg1 = KG(
        entities={
            "000000000000000000000002": entities["000000000000000000000002"],
            "000000000000000000000003": entities["000000000000000000000003"],
        },
        rel=rel_1,
        name="graph1",
    )
    expected_kg2 = KG(entities=entities, rel=rel_2, name="graph2")
    return {
        "000000000000000000000000": expected_kg1,
        "000000000000000000000001": expected_kg2,
    }


@pytest.fixture
def simple_kg():
    entities = {
        "e1": {"my_label": "A", "a1": "first entity", "a2": 123},
        "e2": {"my_label": "A", "a1": "second ent"},
        "e3": {"my_label": "A", "a2": 124},
    }
    rel = {"e1": {"e3": "somerelation"}}
    return {"simple": KG(entities=entities, rel=rel)}


def test_is_gradoop_id():
    assert is_gradoop_id("000000000000000000000000")
    assert is_gradoop_id("00000000000000000000000a")
    assert not is_gradoop_id("1")
    assert not is_gradoop_id("00000000000000000000000x")
    assert not is_gradoop_id(000000000000000000000000)


def test_load_from_gradoop(gradoopy_kg):
    test_data_folder = os.path.join(
        pathlib.Path(__file__).parent.parent.resolve(), "test_data"
    )
    kgs = load_from_csv_datasource(
        os.path.join(test_data_folder, "gradoop_csv"), graph_name_property="a"
    )
    assert kgs["000000000000000000000000"] == gradoopy_kg["000000000000000000000000"]
    assert kgs["000000000000000000000001"] == gradoopy_kg["000000000000000000000001"]


def test_metadata(gradoopy_kg, simple_kg):
    expected_g = {"graph1": [[], []], "graph2": [[], []]}
    expected_v = {
        "A": [["a", "b", "c"], [str, int, float]],
        "B": [["a", "b", "c"], [int, bool, float]],
    }
    expected_e = {"a": [["a", "b"], [int, float]], "b": [["a"], [int]]}
    meta = _create_metadata(gradoopy_kg)
    expected_metadata = {"g": expected_g, "v": expected_v, "e": expected_e}
    assert meta == expected_metadata

    # with custom type
    attr_type_mapping = {
        "v": {"A": {"c": "double"}, "B": {"c": "double"}},
        "e": {"a": {"b": "double"}},
    }
    expected_v_custom = {
        "A": [["a", "b", "c"], [str, int, "double"]],
        "B": [["a", "b", "c"], [int, bool, "double"]],
    }
    expected_e_custom = {
        "a": [["a", "b"], [int, "double"]],
        "b": [["a"], [int]],
    }
    expected_meta_custom = {
        "g": expected_g,
        "v": expected_v_custom,
        "e": expected_e_custom,
    }
    meta_custom = _create_metadata(
        gradoopy_kg, attribute_type_mapping=attr_type_mapping
    )
    assert meta_custom == expected_meta_custom

    # for simple kg with custom label
    expected_simple_v = {
        "A": [["a1", "forayer_id", "a2"], [str, str, int]],
    }
    expected_simple_e = {
        "somerelation": [[], []],
    }
    expected_meta_simple = {
        "g": {"graph1": [[], []]},
        "v": expected_simple_v,
        "e": expected_simple_e,
    }
    meta_simple = _create_metadata(
        simple_kg,
        label_attr="my_label",
        attribute_type_mapping=attr_type_mapping,
        vertex_id_attr_name="forayer_id",
    )
    assert meta_simple == expected_meta_simple


def test_create_metadata_lines():
    metadata = {
        "g": {"graph1": [[], []], "graph2": [[], []]},
        "v": {
            "A": [["a", "b", "c"], [str, int, float]],
            "B": [["a", "b", "c"], [int, bool, float]],
        },
        "e": {"a": [["a", "b"], [int, float]], "b": [["a"], [int]]},
    }
    expected_m_lines = [
        ("g", "graph1", ""),
        ("g", "graph2", ""),
        ("v", "A", "a:string,b:int,c:float"),
        ("v", "B", "a:int,b:boolean,c:float"),
        ("e", "a", "a:int,b:float"),
        ("e", "b", "a:int"),
    ]
    assert expected_m_lines == _create_metadata_lines(metadata)


def vertex_line_sort_key(vl):
    return "".join([vl.id, "".join(vl.graph_ids), vl.type, vl.props])


def edge_line_sort_key(vl):
    return "".join(
        [vl.source_id, vl.target_id, "".join(vl.graph_ids), vl.type, vl.props]
    )


def test_vertex_lines(gradoopy_kg, simple_kg):
    metadata = {
        "A": [["a", "b", "c"], [str, int, float]],
        "B": [["a", "b", "c"], [int, bool, float]],
    }
    v_lines, empty_vid_to_gid = _create_vertex_lines(
        gradoopy_kg, "_label", metadata, None
    )
    assert empty_vid_to_gid == {}
    expected_v_lines = [
        VertexLine(
            "000000000000000000000000",
            ["000000000000000000000001"],
            "A",
            "foo|42|13.37",
        ),
        VertexLine(
            "000000000000000000000001",
            ["000000000000000000000001"],
            "A",
            "bar|23|19.84",
        ),
        VertexLine(
            "000000000000000000000002",
            ["000000000000000000000000", "000000000000000000000001"],
            "B",
            "1234|true|0.123",
        ),
        VertexLine(
            "000000000000000000000003",
            ["000000000000000000000000", "000000000000000000000001"],
            "B",
            "5678|false|4.123",
        ),
        VertexLine(
            "000000000000000000000004", ["000000000000000000000001"], "B", "2342||19.84"
        ),
    ]
    expected_v_lines.sort(key=vertex_line_sort_key)
    v_lines.sort(key=vertex_line_sort_key)
    assert v_lines == expected_v_lines

    metadata_simple = {
        "A": [["a1", "forayer_id", "a2"], [str, str, int]],
    }
    expected_prop_strings = {
        "e1": "first entity|e1|123",
        "e2": "second ent|e2|",
        "e3": "|e3|124",
    }
    adapted_simple_kg = _kgs_dict_to_gradoop_id(simple_kg)
    v_lines_simple, vid_to_gid = _create_vertex_lines(
        adapted_simple_kg,
        "my_label",
        vertex_metadata=metadata_simple,
        vertex_id_attr_name="forayer_id",
    )
    simple_graph_id = set()
    v_lines_dict = {line.id: line for line in v_lines_simple}
    for e_id, e_prop in expected_prop_strings.items():
        line = v_lines_dict[vid_to_gid[e_id]]
        assert is_gradoop_id(line.id)
        assert len(line.graph_ids) == 1
        assert is_gradoop_id(line.graph_ids[0])
        simple_graph_id.add(line.graph_ids[0])
        # there is only one graph
        assert len(simple_graph_id) == 1
        assert line.type == "A"
        assert line.props == e_prop


def test_edge_lines(gradoopy_kg, simple_kg):
    metadata = {
        "a": [["a", "b"], [int, float]],
        "b": [["a"], [int]],
    }
    e_lines = _create_edge_lines(gradoopy_kg, metadata, None)
    expected_e_lines = [
        EdgeLine(
            "uncertain",
            ["000000000000000000000001"],
            "000000000000000000000000",
            "000000000000000000000001",
            "a",
            "1234|13.37",
        ),
        EdgeLine(
            "uncertain",
            ["000000000000000000000001"],
            "000000000000000000000001",
            "000000000000000000000000",
            "a",
            "5678|23.42",
        ),
        EdgeLine(
            "uncertain",
            ["000000000000000000000001"],
            "000000000000000000000001",
            "000000000000000000000002",
            "b",
            "3141",
        ),
        EdgeLine(
            "uncertain",
            ["000000000000000000000000", "000000000000000000000001"],
            "000000000000000000000002",
            "000000000000000000000003",
            "b",
            "2718",
        ),
        EdgeLine(
            "uncertain",
            ["000000000000000000000001"],
            "000000000000000000000004",
            "000000000000000000000000",
            "a",
            "|19.84",
        ),
        EdgeLine(
            "uncertain",
            ["000000000000000000000001"],
            "000000000000000000000004",
            "000000000000000000000000",
            "b",
            "",
        ),
    ]
    assert len(expected_e_lines) == len(e_lines)
    expected_e_lines.sort(key=edge_line_sort_key)
    e_lines.sort(key=edge_line_sort_key)
    for res, exp in zip(e_lines, expected_e_lines):
        assert len(res.id) == 24
        # assuming edge ids are counted up
        # and the id is not high enough to contain
        # characters
        assert hex(int(res.id)).startswith("0x")
        assert res.source_id == exp.source_id
        assert res.target_id == exp.target_id
        assert res.graph_ids == exp.graph_ids
        assert res.props == exp.props

    adapted_simple_kg = _kgs_dict_to_gradoop_id(simple_kg)
    e_lines_simple = _create_edge_lines(
        adapted_simple_kg,
        edge_metadata={"somerelation": [[], []]},
        vid_to_gid={"e1": "000000000000000000000000", "e3": "000000000000000000000002"},
    )
    expected_e_lines = [
        EdgeLine(
            "000000000000000000000000",
            ["000000000000000000000000"],
            "000000000000000000000000",
            "000000000000000000000002",
            "somerelation",
            "",
        )
    ]
    assert e_lines_simple == expected_e_lines


def test_g_lines(gradoopy_kg, simple_kg):
    metadata = {"graph1": [[], []], "graph2": [[], []]}
    expected_g_lines = [
        ("000000000000000000000000", "graph1", ""),
        ("000000000000000000000001", "graph2", ""),
    ]
    assert expected_g_lines == _create_graph_lines(gradoopy_kg, metadata)
    adapted_simple_kg = _kgs_dict_to_gradoop_id(simple_kg)
    expected_simple_lines = [("000000000000000000000000", "test_graph", "")]
    assert expected_simple_lines == _create_graph_lines(
        adapted_simple_kg, metadata, "test_graph"
    )

    metadata = {"graph1": [["a"], [str]], "graph2": [["a"], [str]]}
    expected_g_lines_with_name = [
        ("000000000000000000000000", "graph1", "graph1"),
        ("000000000000000000000001", "graph2", "graph2"),
    ]
    assert expected_g_lines_with_name == _create_graph_lines(
        gradoopy_kg, metadata, graph_name_as_property="a"
    )


def test_from_to_gradoop(tmpdir, gradoopy_kg):
    test_data_folder = os.path.join(
        pathlib.Path(__file__).parent.parent.resolve(), "test_data"
    )
    kgs = load_from_csv_datasource(
        os.path.join(test_data_folder, "gradoop_csv"), graph_name_property="a"
    )
    out_path = os.path.join(tmpdir, "gradoop_out")
    write_to_csv_datasource(
        kgs, out_path, vertex_id_attr_name=None, graph_name_as_property="a"
    )

    kgs2 = load_from_csv_datasource(out_path, graph_name_property="a")
    assert kgs["000000000000000000000000"] == kgs2["000000000000000000000000"]
    assert kgs["000000000000000000000001"] == kgs2["000000000000000000000001"]
