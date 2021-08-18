from typing import Dict, List, Set, Tuple, Union


class ClusterHelper:
    """Convenience class for entity clusters.

    The :class:`ClusterHelper` class holds a dict mapping entities to the respective cluster_id
    and a dict with cluster_id mapping to entity sets.
    The :meth:`.add()` and :meth:`.remove()` keep the respective dicts in sync.

    Attributes
    ----------
    clusters: Dict[str,Set[str]]
        maps cluster id to entity set
    entities: Dict[str,int]
        maps entity id to cluster id

    Examples
    --------
    >>> from forayer.knowledge_graph import ClusterHelper
    >>> ch = ClusterHelper([{"a1", "b1"}, {"a2", "b2"}])
    >>> ch
    {0: {'a1', 'b1'}, 1: {'a2', 'b2'}}

    Add an element to a cluster

    >>> ch.add((0, "c1"))
    >>> ch
    {0: {'a1', 'b1', 'c1'}, 1: {'a2', 'b2'}}

    Add a new cluster

    >>> ch.add({"e2", "f1", "c3"})
    >>> ch
    {0: {'a1', 'b1', 'c1'}, 1: {'a2', 'b2'}, 2: {'f1', 'e2', 'c3'}}

    Remove an element from a cluster

    >>> ch.remove("b1")
    >>> ch
    {0: {'a1', 'c1'}, 1: {'a2', 'b2'}, 2: {'f1', 'e2', 'c3'}}


    Notes
    -----
    Only str are allowed for entity identifiers
    """

    def _from_set_list(self, data: List[Set[Union[str, int]]]):
        for cluster_id, inner in enumerate(data):
            if not isinstance(inner, set):
                raise TypeError(
                    f"Only set is allowed as list element, but got {type(inner)}"
                )
            inner_set = set()
            for inner_element in inner:
                if not isinstance(inner_element, str):
                    raise TypeError(
                        "Only str is allowed as element identifier, but got"
                        f" {type(inner_element)}"
                    )
                inner_element = inner_element
                self.elements[inner_element] = cluster_id
                inner_set.add(inner_element)
            self.clusters[cluster_id] = inner_set

    def _from_dict(self, data: Dict[Union[str, int], Union[str, int]]):
        for cluster_id, dict_items in enumerate(data.items()):
            left, right = dict_items
            if not isinstance(left, str):
                raise TypeError(
                    f"Only str is allowed as element identifier, but got {type(left)}"
                )
            if not isinstance(right, str):
                raise TypeError(
                    f"Only str is allowed as dict value, but got {type(left)}"
                )
            self.elements[left] = cluster_id
            self.clusters[cluster_id] = {left}
            self.elements[right] = cluster_id
            self.clusters[cluster_id].add(right)

    def __init__(
        self,
        data: Union[
            List[Set[Union[str, int]]],
            Dict[Union[str, int], Union[str, int]],
        ] = None,
    ):
        """Initialize a ClusterHelper object with clusters.

        Parameters
        ----------
        data : Union[
                    List[Set[str]],
                    Dict[Union[str, int], Union[str, int]],
                ]
            Clusters either as list of sets, or dict with
            links as key, value pairs
        Raises
        ------
        TypeError
            if data is not dict or list
        """
        self.elements = {}
        self.clusters = {}
        if data is None:
            return
        if not isinstance(data, (dict, list)):
            raise TypeError(f"Only list or dict allowed, but got {type(data)}")
        elif isinstance(data, list):
            self._from_set_list(data)
        elif isinstance(data, dict):
            self._from_dict(data)

    def __repr__(self):
        return str(self.clusters)

    def info(self):
        """Print general information about this object.

        Returns
        -------
        str
            information about number of entities and clusters
        """
        num_elements = len(self.elements)
        num_clusters = len(self.clusters)
        return (
            self.__class__.__name__
            + f"(# elements:{num_elements}, # clusters:{num_clusters})"
        )

    def links(self, key: str) -> Union[str, Set[str]]:
        """Get entities linked to this entity.

        Parameters
        ----------
        key : str
            entity id

        Returns
        -------
        Union[str, Set[str]]
            Either the id of the single linked entity or a set of
            ids if there is more than one link
        """
        cluster = self.clusters[self.elements[key]]
        other_members = cluster.difference({key})
        if len(other_members) == 1:
            return next(iter(other_members))
        return other_members

    def members(self, key: str) -> Set[str]:
        """Get members of a cluster.

        Parameters
        ----------
        key : str
            cluster id

        Returns
        -------
        Set[str]
            cluster members
        """
        return self.clusters[key]

    def __getitem__(self, key):
        if not isinstance(key, (str, int)):
            raise ValueError(f"Only str or int allowed for access, but got {type(key)}")
        elif isinstance(key, str):
            return self.elements[key]
        elif isinstance(key, int):
            return self.clusters[key]

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.elements
        elif isinstance(key, int):
            return key in self.clusters
        return False

    def __setitem__(self, key, value):
        raise TypeError(
            "'ClusterHelper' does not support item assignment use .add() or .remove()"
        )

    def add(
        self,
        new_entry: Union[Tuple[str, str], Set[str]],
    ):
        """Add a new cluster or add element to cluster.

        Parameters
        ----------
        new_entry : Union[Tuple[str, str], Set[str]]
            Either tuple of (cluster_id, new_entity_id), or a new cluster as set

        Raises
        ------
        TypeError
            If len(tuple) > 2
        KeyError
            If cluster_id does not exist
        ValueError
            If cluster id not int or entity id not str
        """
        if not isinstance(new_entry, (tuple, set)):
            raise TypeError(f"Expected tuple or set, but got {type(new_entry)}")
        elif isinstance(new_entry, tuple):
            if len(new_entry) > 2:
                raise TypeError(
                    "Only tuple of len == 2 is allowed, but got {len(new_entry)}"
                )
            if new_entry[0] not in self.clusters:
                raise KeyError(f"Cluster id {new_entry[0]} unknown, cannot add element")
            cluster_id, new_entity = new_entry
            if not isinstance(cluster_id, int):
                raise TypeError(
                    f"Only int allowed as cluster id but got {type(cluster_id)}"
                )
            if not isinstance(new_entity, str):
                raise TypeError(
                    f"Only str allowed as entity id but got {type(new_entity)}"
                )
            self.clusters[cluster_id].add(new_entity)
            self.elements[new_entity] = cluster_id
        else:
            if not len(new_entry.intersection(self.elements.keys())) == 0:
                raise ValueError("Set contains already present entries")
            else:
                cluster_id = max(self.clusters.keys()) + 1
                self.clusters[cluster_id] = set()
                for e in new_entry:
                    if not isinstance(e, str):
                        raise TypeError(
                            f"Only str allowed as entity id but got {type(e)}"
                        )
                    self.elements[e] = cluster_id
                    self.clusters[cluster_id].add(e)

    def remove(self, entry: str):
        """Remove an entity.

        Parameters
        ----------
        entry : str
            entity to remove
        """
        cluster_id = self.elements[entry]
        del self.elements[entry]
        cluster = self.clusters[cluster_id]
        if len(cluster) == 2:
            for member in cluster:
                if member != entry:
                    del self.elements[member]
            del self.clusters[cluster_id]
        else:
            self.clusters[cluster_id].remove(entry)

    def remove_cluster(self, cluster_id: int):
        """Remove an entire cluster with the given cluster id.

        Parameters
        ----------
        cluster_id : int
            id of the cluster to remove
        """
        cluster_elements = self.clusters[cluster_id]
        for e in iter(cluster_elements):
            del self.elements[e]
        del self.clusters[cluster_id]

    def __eq__(self, other):
        if isinstance(other, ClusterHelper):
            return (self.clusters == other.clusters) and (
                self.elements == other.elements
            )
        return False

    def __size__(self):
        return len(self.clusters)
