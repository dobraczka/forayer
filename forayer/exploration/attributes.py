from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from forayer.knowledge_graph import KG, AttributeEmbeddedKG, ERTask
from joblib import Memory
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

memory = Memory("./data/data_frames", mmap_mode="r+")


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


@memory.cache
def _reduce_dim(embeddings):
    return TSNE(n_components=2, n_jobs=-1).fit_transform(
        PCA(n_components=20).fit_transform(embeddings)
    )


def _reduced_embeddings(entities):
    wanted_attr = set(non_nan_embeddings(entities, percent=False, plot=False).index)
    attr_indices = defaultdict(list)
    emb_list = []
    attr_name_to_ent = {}
    for e_id, e_attr_dict in entities.items():
        for a_name, e_attr_value in e_attr_dict.items():
            attr_name_to_ent[a_name] = e_id
            if a_name in wanted_attr and len(wanted_attr) > 0:
                for token_emb in e_attr_value:
                    if not isinstance(token_emb, float):
                        emb_list.append(token_emb)
                        attr_indices[a_name].append(len(emb_list) - 1)
    attr_indices = dict(attr_indices)
    embeddings = np.array(emb_list)
    return _reduce_dim(embeddings), attr_indices, attr_name_to_ent


def _er_task_embedding_df_creation(emb2d, attr_indices, attr_name_to_ent, er_task):
    row = []
    for attr_name, indices in attr_indices.items():
        for _ in indices:
            ent_id = attr_name_to_ent[attr_name]
            # lone entities are assigne to cluster_id -1
            cluster_id = er_task.clusters.get(ent_id, value=-1)
            row.append((ent_id, cluster_id, attr_name))
    attr_emb_dim_red = pd.DataFrame(
        row, columns=["entity_id", "cluster_id", "attribute"]
    )
    emb2d_df = pd.DataFrame(emb2d, columns=["embx", "emby"])
    return attr_emb_dim_red.join(emb2d_df), "cluster_id"


def _embedding_df_creation(emb2d, attr_indices, attr_name_to_ent, entities):
    row = []
    for attr_name, indices in attr_indices.items():
        for _ in indices:
            row.append((attr_name_to_ent[attr_name], attr_name))
    attr_emb_dim_red = pd.DataFrame(row, columns=["entity_id", "attribute"])
    emb2d_df = pd.DataFrame(emb2d, columns=["embx", "emby"])
    return attr_emb_dim_red.join(emb2d_df), "entity_id"


def dim_reduced_embeddings_df(entities):
    """Create a DataFrame with x,y coordinates of dimensionality reduced attribute embeddings.

    Parameters
    ----------
    entities
        Entities with attribute embeddings.

    Returns
    -------
    pd.DataFrame
        df with the columns 'attribute,embx,emby'
    color_col_suggestion
        suggested column for color
    """
    df_creation = _embedding_df_creation
    if isinstance(entities, KG):
        _entities = entities.entities
    elif isinstance(entities, ERTask):
        _entities = entities.all_entities()
        df_creation = _er_task_embedding_df_creation

    emb2d, attr_indices, attr_name_to_ent = _reduced_embeddings(_entities)
    return df_creation(emb2d, attr_indices, attr_name_to_ent, entities)


def plot_attribute_embeddings(entities, subset=None, color_col=None, colorscale=None):
    """Plot attribute embeddings.

    Parameters
    ----------
    entities
        Entities with embedded attributes to plot.
        Can be KG or ERTask.
    subset
        Specify a subset of entity ids to plot, but create the
        dimensionality redcution based on all provided.
    color_col
        Column to use for color. Can be "entity_id, cluster_id or attribute"
    colorscale
        Use a specific color scale
    """
    attr_emb_dim_red, color_col_suggestion = dim_reduced_embeddings_df(entities)
    if subset is not None:
        attr_emb_dim_red = attr_emb_dim_red[attr_emb_dim_red["entity_id"].isin(subset)]
    if color_col is None and color_col_suggestion == "cluster_id":
        actual_color_col = "cluster_id"
    else:
        if color_col == "is_clustered":
            numeric_color = {
                attr: i
                for i, attr in enumerate(list(attr_emb_dim_red["cluster_id"].unique()))
            }
            attr_emb_dim_red["color"] = attr_emb_dim_red[color_col].replace(
                numeric_color
            )
            actual_color_col = "color"
        else:
            color_col = color_col_suggestion if color_col is None else color_col
            numeric_color = {
                attr: i
                for i, attr in enumerate(list(attr_emb_dim_red[color_col].unique()))
            }
            attr_emb_dim_red["color"] = attr_emb_dim_red[color_col].replace(
                numeric_color
            )
            actual_color_col = "color"

    return go.Figure(
        data=go.Scatter(
            x=attr_emb_dim_red["embx"],
            y=attr_emb_dim_red["emby"],
            mode="markers",
            marker_color=attr_emb_dim_red[actual_color_col],
            text=attr_emb_dim_red["attribute"],
            marker_colorscale=colorscale,
        )
    )
