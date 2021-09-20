"""Methods to deal with entity clusters."""

import random
from itertools import chain, combinations
from typing import Any, Dict, Iterable, List, Set, Tuple, Union

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

    If a cluster is present

    >>> {"c1","a1"} in ch
    True

    And even if a link exists or not

    >>> ("f1","e2") in ch
    True
    >>> ("a1","e2") in ch
    False
    """

    def _contains_overlaps(self, data):
        if len(data) > 1 and len(list(chain(*data))) > len(set.union(*data)):
            return True
        return False

    def _from_set_list(self, data: List[Set]):
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
                inner_element = inner_element
                self.elements[inner_element] = cluster_id
                inner_set.add(inner_element)
            self.clusters[cluster_id] = inner_set

    def _from_dict(self, data: Dict):
        for cluster_id, dict_items in enumerate(data.items()):
            left, right = dict_items
            if left == right:
                raise ValueError(f"No selflinks allowed: {left} -> {right}")
            self.elements[left] = cluster_id
            self.clusters[cluster_id] = {left}
            self.elements[right] = cluster_id
            self.clusters[cluster_id].add(right)

    def _from_clusters(self, data: Dict):
        if self._contains_overlaps(data.values()):
            raise ValueError(
                "Entries with multiple memberships are not allowed, when specifying"
                " clusters and ids explicitly"
            )
        self.elements = {
            e_id: cluster_id for cluster_id, cluster in data.items() for e_id in cluster
        }
        self.clusters = data

    def __init__(
        self,
        data: Union[List[Set], Dict] = None,
    ):
        """Initialize a ClusterHelper object with clusters.

        Parameters
        ----------
        data : Union[List[Set], Dict]
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

    def all_pairs(self, key=None) -> Iterable[Tuple[Any, Any]]:
        """Get all entity pairs of a specific cluster or of all clusters.

        Parameters
        ----------
        key
            Cluster id.  If None, provides pairs of all clusters.

        Returns
        -------
        Generator[Tuple[Any, Any]]
            Generator that produces the wanted pairs.
        """
        if key is not None:
            return combinations(self.clusters[key], 2)
        # get pair combinations of clusters and chain generators
        return chain(*[combinations(cluster, 2) for cluster in self.clusters.values()])

    def members(self, key) -> Set:
        """Get members of a cluster.

        Parameters
        ----------
        key
            cluster id

        Returns
        -------
        Set
            cluster members
        """
        return self.clusters[key]

    def __getitem__(self, key):
        """Get cluster members.

        Parameters
        ----------
        key
            Cluster id

        Returns
        -------
        Set
            Cluster members
        """
        return self.clusters[key]

    def get(self, key, value=None):
        """Return cluster's element or default value.

        Tries to return the cluster with the cluster id == key.
        If None is found return provided value.

        Parameters
        ----------
        key
            Searched cluster id.
        value
            Default value to return in case id is not present.

        Returns
        -------
        Set
            Cluster with provided cluster_id.
        """
        try:
            return self[key]
        except KeyError:
            return value

    def __contains__(self, key):
        """Check if entities/links/clusters are contained.

        Parameters
        ----------
        key
            Either entity id, Tuple with two entities to check for a link
            between entities, or a clusters as set of entity ids
        """
        if isinstance(key, Set):
            return key in self.clusters.values()
        elif (
            isinstance(key, Tuple)
            and len(key) == 2
            and key[0] in self.elements
            and key[1] in self.elements
        ):
            return self.elements[key[0]] == self.elements[key[1]]
        else:
            return key in self.elements

    def __setitem__(self, key, value):
        """Not Implemented."""
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

    def merge(self, c1, c2, new_id=None):
        """Merge two clusters.

        Parameters
        ----------
        c1
            Id of one cluster to merge
        c2
            Id of other cluster to merge
        new_id
            New id of cluster, if None take c1

        Raises
        ------
        ValueError
            If cluster id(s) do not exist
        """
        if c1 not in self.clusters or c2 not in self.clusters:
            raise ValueError("Can only merge on existing cluster ids")
        cluster1 = self[c1]
        cluster2 = self[c2]
        if new_id:
            del self.clusters[c1]
            for e1 in cluster1:
                del self.elements[e1]
            self.add(cluster1, c_id=new_id)
        else:
            new_id = c1
        del self.clusters[c2]
        for e2 in cluster2:
            del self.elements[e2]
            self.add_to_cluster(new_id, e2)

    def add_link(self, e1, e2):
        """Add a new entity link.

        Either adds a link to an existing entity or
        creates a new cluster with both.

        Parameters
        ----------
        e1
           Id of one entity that will be linked
        e2
            Id of other entity that will be linked

        Returns
        ------
        c_id
            Id of cluster that was created, or
            of existing cluster that was enhanced
            Returns False if link already was present
        """
        if e1 not in self and e2 not in self:
            return self.add({e1, e2})
        elif e1 in self.elements and e2 in self.elements:
            if (e1, e2) in self:
                return False
            # merging
            cluster_id_1 = self.elements[e1]
            cluster_id_2 = self.elements[e2]
            return self.merge(cluster_id_1, cluster_id_2)
        elif e1 in self.elements:
            cluster_id = self.elements[e1]
            new_entity = e2
        elif e2 in self.elements:
            cluster_id = self.elements[e2]
            new_entity = e1
        self.clusters[cluster_id].add(new_entity)
        self.elements[new_entity] = cluster_id

    def add_to_cluster(self, c_id, new_entity):
        """Add an entity to a cluster.

        Parameters
        ----------
        c_id
            Cluster id where entity will be added
        new_entity
            Id of new entity

        Raises
        ------
        KeyError
            If cluster id unknonw
        ValueError
            If entity already belongs to other cluster
        """
        if c_id not in self.clusters:
            raise KeyError("Cluster id {c_id} unknown")
        if new_entity in self.elements:
            raise ValueError(
                "Entity id {new_entity} already belongs to {self.clusters[c_id]}"
            )
        self.elements[new_entity] = c_id
        self.clusters[c_id].add(new_entity)

    def add(
        self,
        new_entry: Set,
        c_id=None,
    ):
        """Add a new cluster.

        Parameters
        ----------
        new_entry : Set
            New cluster as set

        c_id
           Cluster id that will be assigned.
           If None, the next largest cluster id will be assigned
           Assuming cluster ids are integers

        Raises
        ------
        ValueError
            If entity id already present in other cluster
            Or if new cluster id cannot be inferred automatically
            by incrementing
        """
        if not isinstance(new_entry, set):
            raise TypeError(f"Expected set, but got {type(new_entry)}")
        else:
            if not len(new_entry.intersection(self.elements.keys())) == 0:
                raise ValueError("Set contains already present entries")
            else:
                max_cid = max(self.clusters.keys())
                if not isinstance(max_cid, int):
                    raise ValueError(
                        "Cluster Id cannot be automatically incremented, please provide"
                        " it explicitly"
                    )
                cluster_id = max_cid + 1
                self.clusters[cluster_id] = set()
                for e in new_entry:
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

    def remove_cluster(self, cluster_id):
        """Remove an entire cluster with the given cluster id.

        Parameters
        ----------
        cluster_id
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
