import pytest
from forayer.datasets import OpenEADataset
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

    s_unm = er_task.sample(1, unmatched=1)
    assert len(s_unm.clusters) == 1
    assert len(s_unm.kgs["kg1"]) + len(s_unm.kgs["kg2"]) == 3
    matches = 0
    for k1 in s_unm["kg1"].entities.keys():
        for k2 in s_unm["kg2"].entities.keys():
            if (
                k1 in er_task.clusters
                and k2 in er_task.clusters
                and er_task.clusters[k1] == er_task.clusters[k2]
            ):
                matches += 1
    assert matches == 1


def test_sample_openea():
    ds = OpenEADataset(
        ds_pair="D_W",
        size="15K",
        version=1,
    )
    sampled = ds.er_task.sample(500, unmatched=1000)
    assert len(sampled.clusters) == 500
    # each cluster has two members
    assert len(sampled["DBpedia"]) >= 500
    assert len(sampled["Wikidata"]) >= 500
    assert len(sampled) >= (500 * 2) + 1000


def test_all_entities(er_task):
    expected = {
        "kg_1_e1": {"a1": "first entity", "a2": 123},
        "kg_1_e2": {"a1": "second ent"},
        "kg_1_e3": {"a2": 124},
        "kg_2_e1": {"a5": "first entity", "a2": 123},
        "kg_2_e2": {"a6": "other second ent"},
        "kg_2_e3": {"a7": 123},
    }
    assert er_task.all_entities() == expected


def test_without_match(er_task):
    er_task.without_match() == []
    er_task["kg1"].add_entity("test", {})
    er_task.without_match() == ["test"]
