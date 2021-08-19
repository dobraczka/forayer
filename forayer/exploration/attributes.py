from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from forayer.knowledge_graph import KG, AttributeEmbeddedKG


def non_nan_embeddings(
    kg,
    *,
    percent: bool = True,
    plot: bool = True,
    sort: str = "not nan",
    sort_ascending: bool = False
):
    """Return distribution of found embeddings vs not-found embeddings per attribute.

    For each attribute counts the number of np.NaN  and non-NaN tokens in attribute values.

    Parameters
    ----------
    kg : AttributeEmbeddedKG or dict with entities
        Knowledge graph (or only entities) with attribute values as embeddings.
    percent : bool
        If true give result in percent, else absolute occurence.
    plot : bool
        If true return plot, else return pd.DataFrame.
    sort : str
       Either sort by "nan" or "not nan" if None do not sort.
    sort_ascending : bool
       If True sort ascending.

    Returns
    -------
    non_nan_embeddings
        If plot=True returns a plotly plot
        else returns a df with the information.
    """
    if isinstance(kg, AttributeEmbeddedKG):
        entities = kg.entities
    else:
        entities = kg
    nan_col = "nan"
    not_nan_col = "not nan"
    tmp_total_col = "total"
    test = defaultdict(lambda: defaultdict(int))
    for attr_dict in entities.values():
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
    if sort is not None:
        sort = sort.lower()
        attribute_stat_df = attribute_stat_df.sort_values(
            sort, ascending=sort_ascending
        )
    if plot:
        pd.options.plotting.backend = "plotly"
        return attribute_stat_df.plot(kind="bar")
    return attribute_stat_df


def attribute_distribution(
    kg, *, percent: bool = True, plot: bool = True, sort_ascending: bool = False
):
    """Calculate the occurence of attribute names across entities.

    Parameters
    ----------
    kg : KG or dict with entities.
        Knowledge graph (or only entities) with attribute values as embeddings.
    percent : bool
        If true give result in percent of all attributes, else absolute occurence.
    plot : bool
        If true return plot, else return pd.DataFrame
    sort_ascending : bool
        If true sort_ascending on occurence else, descending

    Returns
    -------
    attr_distribution
        If plot=True returns a plotly plot
        else returns a df with the information.
    """
    if isinstance(kg, KG):
        entities = kg.entities
    else:
        entities = kg
    col_name = "occurence"
    attribute_count = Counter(k for attr in entities.values() for k in attr.keys())
    (index, values) = zip(*dict(attribute_count).items())
    attribute_stat_df = pd.DataFrame(values, columns=[col_name], index=index).fillna(0)
    if percent:
        attribute_stat_df = (attribute_stat_df / len(entities)) * 100
        new_col_name = "present in % of entities"
        attribute_stat_df.rename(columns={col_name: new_col_name}, inplace=True)
        col_name = new_col_name
    attribute_stat_df = attribute_stat_df.sort_values(
        col_name, ascending=sort_ascending
    )
    if plot:
        pd.options.plotting.backend = "plotly"
        return attribute_stat_df.plot(kind="bar")
    return attribute_stat_df
