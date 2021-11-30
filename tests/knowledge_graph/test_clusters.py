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

    # init with ints
    clusters_1 = ClusterHelper([{1, 4}, {2, 5}, {3, 6}])

    assert clusters_1.clusters == {0: {1, 4}, 1: {2, 5}, 2: {3, 6}}

    # overlapping sets
    ch_sets = ClusterHelper(
        [
            {"1", "b3", "a1"},
            {"1", "b1"},
            {"b3", "a1", "b1"},
            {"a1", "b1"},
            {"c1", "e1"},
            {"c1", "d1"},
            {"e1", "d1"},
            {"a2", "2"},
        ]
    )
    expected_clusters = {
        frozenset({"a1", "1", "b1", "b3"}),
        frozenset({"a2", "2"}),
        frozenset({"c1", "d1", "e1"}),
    }
    assert {frozenset(c) for c in ch_sets.clusters.values()} == expected_clusters

    # assert no selflinks
    with pytest.raises(ValueError):
        ClusterHelper({"1": "1"})

    # assert no multiple cluster memberships with cluster init
    with pytest.raises(ValueError):
        ClusterHelper({0: {"1", "2"}, 1: {"1", "3"}})


def test_cluster_links():
    clusters = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
    assert clusters.links("a1") == "1"
    assert clusters.links("1") == "a1"
    assert clusters.links("a1", always_return_set=True) == {"1"}
    with pytest.raises(KeyError):
        print(clusters.links("wrong"))

    clusters_1 = ClusterHelper([{1, 4}, {2, 5}, {3, 6}])
    assert clusters_1.links(1) == 4
    assert clusters_1.links(4) == 1
    assert clusters_1.links(1, always_return_set=True) == {4}
    with pytest.raises(KeyError):
        print(clusters_1.links("wrong"))


def test_cluster_members():
    clusters = ClusterHelper([{"a1", "1"}, {"a2", "2"}, {"a3", "3"}])
    assert clusters.members(clusters.elements["a1"]) == {"a1", "1"}

    clusters_1 = ClusterHelper([{1, 4}, {2, 5}, {3, 6}])
    assert clusters_1.members(clusters_1.elements[1]) == {1, 4}


def test_cluster_element_add():
    clusters_1 = ClusterHelper([{"a2", "2"}, {"a3", "3"}])
    clusters_1.add({"a1", "1", "d"})

    assert clusters_1.links("a1") == {"1", "d"}


def test_add_to_cluster():
    clusters_1 = ClusterHelper([{1, 4}, {2, 5}, {3, 6}])
    clusters_1.add_to_cluster(clusters_1.elements[1], "d")
    assert clusters_1.links(1) == {4, "d"}
    clusters_2 = ClusterHelper([{2, 5}, {3, 6}])
    clusters_2.add({1, 4, "d"})

    assert clusters_1.links(1) == clusters_2.links(1)

    # no merging
    with pytest.raises(ValueError):
        clusters_1.add_to_cluster(clusters_1.elements[2], 1)


def test_merge():
    cluster = ClusterHelper({0: {1, 2}, 1: {3, 4}})
    with pytest.raises(ValueError):
        cluster.merge(2, 3)
    with pytest.raises(ValueError):
        cluster.merge(1, 3)
    with pytest.raises(ValueError):
        cluster.merge(3, 1)

    cluster.merge(0, 1)
    assert cluster == ClusterHelper({0: {1, 2, 3, 4}})

    cluster = ClusterHelper({0: {1, 2}, 1: {3, 4}})
    cluster.merge(0, 1, new_id=2)
    assert cluster == ClusterHelper({2: {1, 2, 3, 4}})


def test_add_link():
    cluster = ClusterHelper({0: {1, 2}})

    # entirely new
    cluster.add_link(3, 4)
    assert cluster.elements[3] == cluster.elements[4]
    assert cluster[1] == {3, 4}

    # add to existing
    cluster.add_link(3, 5)
    assert cluster.elements[3] == cluster.elements[5]
    assert cluster[1] == {3, 4, 5}

    # merge
    cluster.add_link(1, 3)
    assert cluster == ClusterHelper({0: {1, 2, 3, 4, 5}})


def test_get():
    clusters = ClusterHelper({0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}})
    assert clusters.get(0) == {"a1", "1"}
    assert clusters.get(0, value={}) == {"a1", "1"}
    assert clusters.get("a1") is None
    assert clusters.get("a1", value=-1) == -1

    assert clusters.get(3) is None
    assert clusters.get(3, value={}) == {}


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


def test_number_of_links():
    clusters = {0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}}
    ch = ClusterHelper(clusters)
    assert ch.number_of_links == 3
    ch.add({"a4", "4"})
    assert ch.number_of_links == 4
    ch.add_to_cluster(0, "a5")
    ch.add_to_cluster(0, "a6")
    assert ch.number_of_links == 9


def assert_equal_pairs(actual, desired):
    actual = list(actual)
    assert len(actual) == len(desired)
    actual_set = {frozenset(p) for p in actual}
    desired_set = {frozenset(p) for p in desired}
    assert actual_set == desired_set


def test_get_all_pairs():
    clusters = {0: {"a1", "1"}, 1: {"a2", "2"}, 2: {"a3", "3"}}
    ch = ClusterHelper(clusters)
    all_pairs = ch.all_pairs()
    assert_equal_pairs(all_pairs, [("a1", "1"), ("a2", "2"), ("a3", "3")])

    all_pairs = ch.all_pairs(0)
    assert_equal_pairs(all_pairs, [("a1", "1")])

    clusters = {0: {"a1", "1", "b1", "b3"}, 1: {"a2", "2"}, 2: {"a3", "3"}}
    ch = ClusterHelper(clusters)
    all_pairs = ch.all_pairs()
    assert_equal_pairs(
        all_pairs,
        [
            ("a1", "1"),
            ("a1", "b1"),
            ("a1", "b3"),
            ("1", "b1"),
            ("1", "b3"),
            ("b1", "b3"),
            ("a2", "2"),
            ("a3", "3"),
        ],
    )

    all_pairs = ch.all_pairs(0)
    assert_equal_pairs(
        all_pairs,
        [
            ("a1", "1"),
            ("a1", "b1"),
            ("a1", "b3"),
            ("1", "b1"),
            ("1", "b3"),
            ("b1", "b3"),
        ],
    )


def test_contains():
    ch = ClusterHelper({0: {"a1", "1", "b1", "b3"}, 1: {2, 3}, 2: {"a3", "3"}})
    assert "1" in ch
    assert "5" not in ch
    assert 5 not in ch
    assert ("a1", "1") in ch
    assert {"a1", "1", "b1", "b3"} in ch
    assert 2 in ch
    assert (2, 3) in ch
    assert {2, 3} in ch


def test_clone():
    ch = ClusterHelper({0: {"a1", "1", "b1", "b3"}, 1: {2, 3}, 2: {"a3", "3"}})
    cloned = ch.clone()
    assert ch == cloned
    cloned.remove(2)
    assert ch != cloned
