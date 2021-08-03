import pytest
from forayer.knowledge_graph import Clusters


def test_clusters_init():
    link_dict = {"a1": "1", "a2": "2", "a3": "3"}
    link_dict_with_ints = {"a1": 1, "a2": 2, "a3": 3}
    clusters_from_dict = Clusters(link_dict)
    cluster_from_list_set = Clusters([{a, b} for a, b in link_dict.items()])
    clusters_from_dict_with_ints = Clusters(link_dict_with_ints)
    cluster_from_list_set_with_ints = Clusters(
        [{a, b} for a, b in link_dict_with_ints.items()]
    )

    assert clusters_from_dict == cluster_from_list_set
    assert clusters_from_dict == clusters_from_dict_with_ints
    assert clusters_from_dict == cluster_from_list_set_with_ints

    # multiple
    list_set = [{"a1", 1, 5}, {"a2", 2}, {"a3", 3}]
    cluster_from_list_set_mult = Clusters(list_set)
    assert cluster_from_list_set_mult["a1"] == {"1", "5"}


def test_cluster_access():
    clusters = Clusters({"a1": "1", "a2": "2", "a3": "3"})
    assert clusters["a1"] == "1"
    assert clusters["1"] == "a1"
    with pytest.raises(KeyError):
        print(clusters["wrong"])


def test_cluster_element_add():
    clusters_1 = Clusters({"a1": "1", "a2": "2", "a3": "3"})
    clusters_1.add(("c1", "d"))
    assert clusters_1["c1"] == "d"
    assert clusters_1["d"] == "c1"

    clusters_2 = Clusters({"a1": "1", "a2": "2", "a3": "3"})
    clusters_2.add({"c1", "d"})

    assert clusters_1 == clusters_2


def test_cluster_element_remove():
    clusters_1 = Clusters({"a1": "1", "a2": "2", "a3": "3"})
    clusters_1.remove("a1")

    with pytest.raises(KeyError):
        clusters_1["a1"]

    with pytest.raises(KeyError):
        clusters_1["1"]

    clusters_2 = Clusters([{"a1", "1", "5"}, {"a2", "2"}, {"a3", "3"}])
    clusters_2.remove("a1")

    with pytest.raises(KeyError):
        clusters_2["a1"]

    assert clusters_2["1"] == "5"
