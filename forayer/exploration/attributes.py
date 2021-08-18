from collections import defaultdict
from typing import Union

import numpy as np
import pandas as pd
from forayer.knowledge_graph import KG, AttributeEmbeddedKG


def non_nan_embeddings(
    kg: AttributeEmbeddedKG,
    *,
    percent=True,
    plot=True,
    sort="not nan",
    sort_ascending=False
):
    nan_col = "nan"
    not_nan_col = "not nan"
    tmp_total_col = "total"
    test = defaultdict(lambda: defaultdict(int))
    for attr_dict in kg.entities.values():
        for attr_name, attr_value in attr_dict.items():
            if len(attr_value) == 0:
                test[attr_name][nan_col] += 1
                test[attr_name][not_nan_col] = 0
            for token in attr_value:
                if isinstance(token, np.ndarray):
                    test[attr_name][not_nan_col] += 1
                else:
                    test[attr_name][nan_col] += 1
    attribute_stat_df = pd.DataFrame(test).fillna(0).T
    if percent:
        attribute_stat_df[tmp_total_col] = (
            attribute_stat_df[nan_col] + attribute_stat_df[not_nan_col]
        )
        attribute_stat_df[nan_col] = (
            attribute_stat_df[nan_col] / attribute_stat_df[tmp_total_col]
        ) * 100
        attribute_stat_df[not_nan_col] = (
            attribute_stat_df[not_nan_col] / attribute_stat_df[tmp_total_col]
        ) * 100
        del attribute_stat_df[tmp_total_col]
        attribute_stat_df = attribute_stat_df.sort_values(
            sort, ascending=sort_ascending
        )
    if plot:
        pd.options.plotting.backend = "plotly"
        return attribute_stat_df.plot(kind="bar")
    return attribute_stat_df


def attribute_distribution(kg: KG, *, percent=True, plot=True, sort_ascending=False):
    col_name = "occurence"
    attribute_count = defaultdict(int)
    for attr_dict in kg.entities.values():
        for attr_name, _ in attr_dict.items():
            attribute_count[attr_name] += 1
    (index, values) = zip(*attribute_count.items())
    attribute_stat_df = pd.DataFrame(values, columns=[col_name], index=index).fillna(0)
    if percent:
        attribute_stat_df = (
            attribute_stat_df / attribute_stat_df.sum()[col_name]
        ) * 100
        attribute_stat_df = attribute_stat_df.sort_values(
            "occurence", ascending=sort_ascending
        )
        attribute_stat_df.rename(
            columns={col_name: "% occurence of all attributes"}, inplace=True
        )
    if plot:
        pd.options.plotting.backend = "plotly"
        return attribute_stat_df.plot(kind="bar")
    return attribute_stat_df
