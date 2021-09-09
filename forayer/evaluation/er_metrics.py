"""Implementation of common entity resolution metrics."""
from typing import Dict

from forayer.knowledge_graph import ClusterHelper, ERTask


def _tp_fp_fn(res: ClusterHelper, gold: ClusterHelper, only_tp_fp=False):
    tp = 0
    fp = 0
    fn = 0
    for pairs in res.all_pairs():
        if pairs in gold:
            tp += 1
        else:
            fp += 1
    if only_tp_fp:
        return tp, fp
    for pairs in gold.all_pairs():
        if pairs not in res:
            fn += 1
    return tp, fp, fn


def match_quality(res: ClusterHelper, gold: ClusterHelper) -> Dict:
    """Calculate match quality metrics.

    Parameters
    ----------
    res : ClusterHelper
        Result that should be measured.
    gold : ClusterHelper
        Perfect matches.

    Returns
    -------
    Dict
        Dictionary with metrics "fmeasure","prec" and "rec"

    """
    if len(res) == 0:
        return {"fmeasure": 0.0, "prec": 1.0, "rec": 0.0}
    if len(gold) == 0:
        return {"fmeasure": 0.0, "prec": 0.0, "rec": 0.0}
    tp, fp, fn = _tp_fp_fn(res, gold)
    prec = tp / (tp + fp)
    rec = tp / (tp + fn)
    if prec + rec == 0:
        fm = 0
    else:
        fm = 2 * (prec * rec) / (prec + rec)
    return {"fmeasure": fm, "prec": prec, "rec": rec}


def p_e_ratio(blocks: ClusterHelper, task: ERTask) -> float:
    """Calculate Pair/Entity ratio.

    Parameters
    ----------
    blocks : ClusterHelper
        ClusterHelper with block assignment
    task : ERTask
        Related entity resolution task.

    Returns
    -------
    float
        Pair/Entity ratio

    Raises
    ------
    ZeroDivisionError
        If task has length of zero
    """
    return blocks.number_of_links / len(task)
