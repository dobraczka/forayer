import pytest
from forayer.knowledge_graph import ClusterHelper


def test_clusters_init():
    clusters_1 = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])

    assert clusters_1.clusters == {0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}}
    clusters_2 = ClusterHelper({"a1": "1", "a2": "2", "a3": "3"})
    clusters_3 = ClusterHelper({0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}})
    assert clusters_1 == clusters_2
    assert clusters_1 == clusters_3

    assert clusters_1.clusters == {0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}}

    # multiple
    list_set = [{"a1", "b1", "b5"}, {"a2", "b2"}, {"a3", "b3"}]
    cluster_from_list_set_mult = ClusterHelper(list_set)
    assert cluster_from_list_set_mult.links("a1") == {"b1", "b5"}

    with pytest.raises(TypeError):
        ClusterHelper([{"a1", 1}])


def test_cluster_links():
    clusters = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
    assert clusters.links("a1") == "1"
    assert clusters.links("1") == "a1"
    assert clusters.links("a1", always_return_set=True) == {"1"}
    with pytest.raises(KeyError):
        print(clusters.links("wrong"))


def test_cluster_members():
    clusters = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
    assert clusters.members(clusters["a1"]) == {"a1", "1"}


def test_cluster_element_add():
    clusters_1 = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
    clusters_1.add((clusters_1["a1"], "d"))
    assert clusters_1.links("a1") == {"1", "d"}

    clusters_2 = ClusterHelper([{"a2", "2"}, {"a3", "3"}])
    clusters_2.add({"a1", "1", "d"})

    assert clusters_1.links("a1") == clusters_2.links("a1")


def test_get():
    clusters = ClusterHelper({0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}})
    assert clusters.get(0) == {"a1", "1"}
    assert clusters.get(0, value={}) == {"a1", "1"}
    assert clusters.get("a1") == 0
    assert clusters.get("a1", value=-1) == 0

    assert clusters.get(3) == None
    assert clusters.get(3, value={}) == {}
    assert clusters.get("test") == None
    assert clusters.get("test", value=-1) == -1


def test_cluster_element_remove():
    clusters_1 = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
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


def test_sample():
    clusters = {0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}}
    ch = ClusterHelper(clusters)
    samp = ch.sample(1)
    c_id = list(samp.clusters.keys())[0]
    assert len(samp) == 1
    assert c_id in clusters
    assert samp[c_id] == clusters[c_id]
