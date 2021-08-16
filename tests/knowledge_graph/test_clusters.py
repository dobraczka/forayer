import pytest
from forayer.knowledge_graph import ClusterHelper


def test_clusters_init():
    link_dict = {"a1": "1", "a2": "2", "a3": "3"}
    link_dict_with_ints = {"a1": 1, "a2": 2, "a3": 3}
    clusters_from_dict = ClusterHelper(link_dict)
    cluster_from_list_set = ClusterHelper([{a, b} for a, b in link_dict.items()])
    clusters_from_dict_with_ints = ClusterHelper(link_dict_with_ints)
    cluster_from_list_set_with_ints = ClusterHelper(
        [{a, b} for a, b in link_dict_with_ints.items()]
    )

    assert clusters_from_dict == cluster_from_list_set
    assert clusters_from_dict == clusters_from_dict_with_ints
    assert clusters_from_dict == cluster_from_list_set_with_ints

    # multiple
    list_set = [{"a1", 1, 5}, {"a2", 2}, {"a3", 3}]
    cluster_from_list_set_mult = ClusterHelper(list_set)
    assert cluster_from_list_set_mult.links("a1") == {"1", "5"}


def test_cluster_links():
    clusters = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    assert clusters.links("a1") == "1"
    assert clusters.links("1") == "a1"
    with pytest.raises(KeyError):
        print(clusters.links("wrong"))


def test_cluster_members():
    clusters = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    assert clusters.members(clusters["a1"]) == {"a1", "1"}


def test_cluster_element_add():
    clusters_1 = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    clusters_1.add(("c1", "d"))
    assert clusters_1.links("c1") == "d"
    assert clusters_1.links("d") == "c1"

    clusters_2 = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    clusters_2.add({"c1", "d"})

    assert clusters_1 == clusters_2


def test_cluster_element_remove():
    clusters_1 = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    clusters_1.remove("a1")

    with pytest.raises(KeyError):
        clusters_1.links("a1")

    with pytest.raises(KeyError):
        clusters_1.links("1")

    clusters_2 = ClusterHelper([{"a1", "1", "5"}, {"a2", "2"}, {"a3", "3"}])
    clusters_2.remove("a1")

    with pytest.raises(KeyError):
        clusters_2.links("a1")

    assert clusters_2.links("1") == "5"


def test_cluster_removal():
    ch = ClusterHelper([{"a1", "b1", "b5"}, {"a2", "b2"}, {"a3", "b3"}])
    ch.remove_cluster(ch.elements["a1"])
    assert "a1" not in ch
    assert "b1" not in ch
    assert "b5" not in ch
