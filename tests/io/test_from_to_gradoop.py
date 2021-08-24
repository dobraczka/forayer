import os
import pathlib

from forayer.io.from_to_gradoop import load_from_csv_datasource
from forayer.knowledge_graph import KG


def test_load_from_gradoop():
    test_data_folder = os.path.join(
        pathlib.Path(__file__).parent.parent.resolve(), "test_data"
    )
    entities = {
        "000000000000000000000000": {"_label": "A", "a": "foo", "b": 42, "c": 13.37},
        "000000000000000000000001": {"_label": "A", "a": "bar", "b": 23, "c": 19.84},
        "000000000000000000000002": {"_label": "B", "a": 1234, "b": True, "c": 0.123},
        "000000000000000000000003": {"_label": "B", "a": 5678, "b": False, "c": 4.123},
        "000000000000000000000004": {"_label": "B", "a": 2342, "c": 19.84},
    }
    rel_1 = {
        "000000000000000000000002": {
            "000000000000000000000003": {"_label": "b", "a": 2718}
        },
    }
    rel_2 = {
        "000000000000000000000000": {
            "000000000000000000000001": {"_label": "a", "a": 1234, "b": 13.37}
        },
        "000000000000000000000001": {
            "000000000000000000000000": {"_label": "a", "a": 5678, "b": 23.42},
            "000000000000000000000002": {"_label": "b", "a": 3141},
        },
        "000000000000000000000002": {
            "000000000000000000000003": {"_label": "b", "a": 2718}
        },
        "000000000000000000000004": {
            "000000000000000000000000": [{"_label": "a", "b": 19.84}, {"_label": "b"}],
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
    kgs = load_from_csv_datasource(
        os.path.join(test_data_folder, "gradoop_csv"), graph_name_property="a"
    )
    assert kgs["000000000000000000000000"] == expected_kg1
    assert kgs["000000000000000000000001"] == expected_kg2
