import random
from itertools import chain, combinations
from typing import Dict, Iterable, List, Set, Tuple, Union

from forayer.knowledge_graph.graph_based_clustering import (
    connected_components_from_container,
)
from forayer.utils.random_help import random_generator


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
    >>> print(ch)
    {0: {'a1', 'b1'}, 1: {'a2', 'b2'}}

    Add an element to a cluster

    >>> ch.add((0, "c1"))
    >>> print(ch)
    {0: {'a1', 'b1', 'c1'}, 1: {'a2', 'b2'}}

    Add a new cluster

    >>> ch.add({"e2", "f1", "c3"})
    >>> print(ch)
    {0: {'a1', 'b1', 'c1'}, 1: {'a2', 'b2'}, 2: {'f1', 'e2', 'c3'}}

    Remove an element from a cluster

    >>> ch.remove("b1")
    >>> print(ch)
    {0: {'a1', 'c1'}, 1: {'a2', 'b2'}, 2: {'f1', 'e2', 'c3'}}

    The __contains__ function is smartly overloaded. You can
    check if an entity is in the ClusterHelper

    >>> "a1" in ch
    True

    If a cluster_id is contained

    >>> 0 in ch
    True

    If a cluster is present

    >>> {"c1","a1"} in ch
    True

    And even if a link exists or not

    >>> ("f1","e2") in ch
    True
    >>> ("a1","e2") in ch
    False


    Notes
    -----
    Only str are allowed for entity identifiers
    """

    def _check_entity_id_type(self, e_id):
        """Check if entity id is str.

        Parameters
        ----------
        e_id
           entity id to check

        Returns
        -------
        e_id
            If e_id is str

        Raises
        ------
        TypeError
            If e_id is not str
        """
        if not isinstance(e_id, str):
            raise TypeError(
                f"Only str is allowed as element identifier, but got {type(e_id)}"
            )
        return e_id

    def _contains_overlaps(self, data):
        if len(data) > 1 and len(list(chain(*data))) > len(set.union(*data)):
            return True
        return False

    def _from_set_list(self, data: List[Set[Union[str, int]]]):
        # check if contains overlaps
        if self._contains_overlaps(data):
            # merge overlapping
            data = connected_components_from_container(data)

        for cluster_id, inner in enumerate(data):
            if not isinstance(inner, set):
                raise TypeError(
                    f"Only set is allowed as list element, but got {type(inner)}"
                )
            inner_set = set()
            for inner_element in inner:
                self._check_entity_id_type(inner_element)
                inner_element = inner_element
                self.elements[inner_element] = cluster_id
                inner_set.add(inner_element)
            self.clusters[cluster_id] = inner_set

    def _from_dict(self, data: Dict[str, str]):
        for cluster_id, dict_items in enumerate(data.items()):
            left, right = dict_items
            if left == right:
                raise ValueError(f"No selflinks allowed: {left} -> {right}")
            self._check_entity_id_type(left)
            if not isinstance(right, str):
                raise TypeError(
                    f"Only str is allowed as dict value, but got {type(left)}"
                )
            self.elements[left] = cluster_id
            self.clusters[cluster_id] = {left}
            self.elements[right] = cluster_id
            self.clusters[cluster_id].add(right)

    def _from_clusters(self, data: Dict[int, Set[str]]):
        if self._contains_overlaps(data.values()):
            raise ValueError(
                "Entries with multiple memberships are not allowed, when specifying"
                " clusters and ids explicitly"
            )
        self.elements = {
            self._check_entity_id_type(e_id): int(cluster_id)
            for cluster_id, cluster in data.items()
            for e_id in cluster
        }
        self.clusters = data

    def __init__(
        self,
        data: Union[List[Set[str]], Dict[str, str], Dict[int, Set[str]]] = None,
    ):
        """Initialize a ClusterHelper object with clusters.

        Parameters
        ----------
        data : Union[List[Set[str]], Dict[str, str], Dict[int,Set[str]]]
            Clusters either as list of sets, or dict with
            links as key, value pairs, or dict with cluster id and set of members

        Raises
        ------
        TypeError
            if data is not dict or list
        ValueError
            For dict[cluster_id,member_set] if overlaps between clusters

        Notes
        -----
        Will try to merge clusters transitively if necessary.
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
            if isinstance(list(data.values())[0], set):
                self._from_clusters(data)
            else:
                self._from_dict(data)

    def __repr__(self):
        return f"ClusterHelper(elements={str(self.elements)},clusters={str(self.clusters)})"

    def __str__(self):
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

    def links(self, key: str, always_return_set=False) -> Union[str, Set[str]]:
        """Get entities linked to this entity.

        Parameters
        ----------
        key : str
            entity id

        always_return_set: str
            If True, return set even if only one entity is contained
        Returns
        -------
        Union[str, Set[str]]
            Either the id of the single linked entity or a set of
            ids if there is more than one link
            If always_return_set is True, will always return set
        """
        cluster = self.clusters[self.elements[key]]
        other_members = cluster.difference({key})
        if not always_return_set and len(other_members) == 1:
            return next(iter(other_members))
        return other_members

    def all_pairs(self, key: Union[str, int] = None) -> Iterable[Tuple[str, str]]:
        """Get all entity pairs of a specific cluster or of all clusters.

        Parameters
        ----------
        key : Union[str, int]
            Entity id or cluster id.
            If None, provides pairs of all clusters.

        Returns
        -------
        Generator[Tuple[str, str]]
            Generator that produces the wanted pairs.
        """
        if key is not None:
            if isinstance(key, int):
                return combinations(self.clusters[key], 2)
            elif isinstance(key, str):
                return combinations(self.clusters[self.elements[key]], 2)
        # get pair combinations of clusters and chain generators
        return chain(*[combinations(cluster, 2) for cluster in self.clusters.values()])

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

    def get(self, key: Union[str, int], value=None):
        """Return entitiy's cluster id or cluster's element or default value.

        If key is str, tries to return the cluster id of the entity.
        If key is int, tries to return the cluster with the cluster id == key.
        If None is found return provided value.

        Parameters
        ----------
        key : Union[str,int]
            Searched key.
        value
            Default value to return in case key is not present.

        Returns
        -------
        Union[int, Set[str]]
            Entity's cluster id or cluster with provided cluster_id.
        """
        try:
            return self[key]
        except KeyError:
            return value

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.elements
        elif isinstance(key, int):
            return key in self.clusters
        elif isinstance(key, Set):
            return key in self.clusters.values()
        elif (
            isinstance(key, Tuple)
            and len(key) == 2
            and isinstance(key[0], str)
            and isinstance(key[1], str)
            and key[0] in self.elements
            and key[1] in self.elements
        ):
            return self.elements[key[0]] == self.elements[key[1]]
        return False

    def __setitem__(self, key, value):
        raise TypeError(
            "'ClusterHelper' does not support item assignment use .add() or .remove()"
        )

    def sample(self, n: int, seed: Union[int, random.Random] = None):
        """Sample n clusters.

        Parameters
        ----------
        n : int
            Number of clusters to return.
        seed : Union[int, random.Random]
            Seed for randomness or seeded random.Random object.
            Default is None.

        Returns
        -------
        ClusterHelper
           ClusterHelper with n clusters.
        """
        r_gen = random_generator(seed)
        return ClusterHelper(
            {c_id: cluster for c_id, cluster in r_gen.sample(self.clusters.items(), n)}
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

    def __len__(self):
        return len(self.clusters)

    @property
    def number_of_links(self):
        """Return the total number of links."""

        def number_of_pairs_in_set(s):
            n = len(s)
            return int(n * (n - 1) / 2)

        return sum(map(number_of_pairs_in_set, self.clusters.values()))
