import pytest
from forayer.knowledge_graph import KG, ClusterHelper, ERTask

@pytest.fixture
def er_task():
    entities_1 = {
        "kg_1_e1": {"a1": "first entity", "a2": 123},
        "kg_1_e2": {"a1": "second ent"},
        "kg_1_e3": {"a2": 124},
    }
    kg1 = KG(entities_1, {"kg_1_e1": {"kg_1_e3": "somerelation"}}, name="kg1")

    entities_2 = {
        "kg_2_e1": {"a5": "first entity", "a2": 123},
        "kg_2_e2": {"a6": "other second ent"},
        "kg_2_e3": {"a7": 123},
    }
    kg2 = KG(entities_2, {"kg_2_e1": {"kg_2_e3": "someotherrelation"}}, name="kg2")

    ert = ERTask(
        [kg1, kg2],
        ClusterHelper(
            [{"kg_1_e1", "kg_2_e1"}, {"kg_1_e2", "kg_2_e2"}, {"kg_1_e3", "kg_2_e3"}]
        ),
    )
    return ert


def test_er_task_inverse_attr(er_task):
    assert er_task.inverse_attr_dict() == {
        "first entity": {"kg1": {"a1": ["kg_1_e1"]}, "kg2": {"a5": ["kg_2_e1"]}},
        123: {
            "kg1": {"a2": ["kg_1_e1"]},
            "kg2": {"a2": ["kg_2_e1"], "a7": ["kg_2_e3"]},
        },
        "second ent": {"kg1": {"a1": ["kg_1_e2"]}},
        "other second ent": {"kg2": {"a6": ["kg_2_e2"]}},
        124: {"kg1": {"a2": ["kg_1_e3"]}},
    }


def test_sample(er_task):
    sampled = er_task.sample(1)
    assert len(sampled.clusters) == 1
    assert len(sampled.kgs["kg1"]) == 1
    assert len(sampled.kgs["kg2"]) == 1
