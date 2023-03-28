import pytest
from numpy.testing import assert_almost_equal

from forayer.evaluation import match_quality, p_e_ratio
from forayer.knowledge_graph import KG, ClusterHelper, ERTask


@pytest.fixture
def res_and_gold():
    res_empty = ClusterHelper()
    one_large = ClusterHelper(
        [{"a1", "b1", "a2", "b2", "a3", "b3", "a4", "b4", "a5", "b5"}]
    )
    half_right_half_wrong = ClusterHelper(
        [
            {"a1", "b1"},
            {"a2", "b2"},
            {"a3", "b3"},
            {"a4", "b5"},
            {"a5", "b4"},
            {"a6", "b6"},
        ]
    )
    all_wrong = ClusterHelper(
        [{"a1", "b2"}, {"a2", "b3"}, {"a3", "b4"}, {"a4", "b5"}, {"a5", "b1"}]
    )
    gold = ClusterHelper(
        [{"a1", "b1"}, {"a2", "b2"}, {"a3", "b3"}, {"a4", "b4"}, {"a5", "b5"}]
    )
    return res_empty, one_large, half_right_half_wrong, all_wrong, gold


def test_metrics(res_and_gold):
    res_empty, one_large, half_right_half_wrong, all_wrong, gold = res_and_gold
    mq = match_quality(res_empty, gold)
    assert mq["prec"] == 1.0
    assert mq["rec"] == 0.0
    assert mq["fmeasure"] == 0.0

    mq = match_quality(one_large, gold)
    assert_almost_equal(mq["prec"], 5 / 45)
    assert mq["rec"] == 1.0
    assert_almost_equal(mq["fmeasure"], 0.199999999, decimal=6)

    mq = match_quality(half_right_half_wrong, gold)
    assert mq["prec"] == 0.5
    assert mq["rec"] == 0.6
    assert_almost_equal(mq["fmeasure"], 0.545454545454, decimal=6)

    mq = match_quality(all_wrong, gold)
    assert mq["prec"] == 0.0
    assert mq["rec"] == 0.0
    assert mq["fmeasure"] == 0.0

    mq = match_quality(gold, gold)
    assert mq["prec"] == 1.0
    assert mq["rec"] == 1.0
    assert mq["fmeasure"] == 1.0

    mq = match_quality(gold, res_empty)
    assert mq["rec"] == 0.0
    assert mq["prec"] == 0.0
    assert mq["fmeasure"] == 0.0


def test_p_e_ratio():
    kg1 = KG({"a1": {}, "a2": {}, "a3": {}, "a4": {}, "a5": {}})
    kg2 = KG({"b1": {}, "b2": {}, "b3": {}, "b4": {}, "b5": {}})
    ert = ERTask([kg1, kg2], ClusterHelper())

    blocks = ClusterHelper(
        [{"a1", "b1"}, {"a2", "b2"}, {"a3", "b3"}, {"a4", "b4"}, {"a5", "b5"}]
    )
    assert p_e_ratio(blocks, ert) == 0.5
