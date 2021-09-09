import networkx as nx
from networkx.algorithms.components.connected import connected_components


def to_graph(elements):
    """.

    Parameters
    ----------
    elements :
        elements
    """
    G = nx.Graph()
    for part in elements:
        # each sublist is a bunch of nodes
        G.add_nodes_from(part)
        # it also imlies a number of edges:
        G.add_edges_from(to_edges(part))
    return G


def to_edges(elements):
    """Treat elements as graph and return it's edges.

    Parameters
    ----------
    elements
        Container with elements

    Examples
    --------
    >>> to_edges(['a','b','c','d'])
    [(a,b), (b,c),(c,d)]
    """
    it = iter(elements)
    last = next(it)

    for current in it:
        yield last, current
        last = current


def connected_components_from_container(elements):
    # https://stackoverflow.com/a/4843408
    G = to_graph(elements)
    return connected_components(G)
