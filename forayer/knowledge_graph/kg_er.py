from typing import Dict, Iterable, List, Set, Tuple, Union


class Clusters:
    def _from_set_list(self, data: List[Set[Union[str, int]]]):
        for cluster_id, inner in enumerate(data):
            if not isinstance(inner, set):
                raise TypeError(
                    f"Only set is allowed as list element, but got {type(inner)}"
                )
            inner_set = set()
            for inner_element in inner:
                if not isinstance(inner_element, (str, int)):
                    raise TypeError(
                        "Only str or int is allowed as element identifier, but got"
                        f" {type(inner_element)}"
                    )
                inner_element = str(inner_element)
                self.ele_to_cluster_id[inner_element] = cluster_id
                inner_set.add(inner_element)
            self.cluster_to_ele[cluster_id] = inner_set

    def _from_dict(self, data: Dict[Union[str, int], Union[str, int]]):
        for cluster_id, dict_items in enumerate(data.items()):
            left, right = dict_items
            left = str(left)
            self.ele_to_cluster_id[left] = cluster_id
            self.cluster_to_ele[cluster_id] = {left}
            if not isinstance(left, (str, int)):
                raise TypeError(
                    "Only str or int is allowed as element identifier, but got"
                    f" {type(left)}"
                )
            if not isinstance(right, (str, int)):
                raise TypeError(
                    "Only str,int or Iterable is allowed as dict value, but got"
                    f" {type(left)}"
                )
            right = str(right)
            self.ele_to_cluster_id[right] = cluster_id
            self.cluster_to_ele[cluster_id].add(right)

    def __init__(
        self,
        data: Union[
            List[Set[Union[str, int]]],
            Dict[Union[str, int], Union[str, int]],
        ] = None,
    ):
        self.ele_to_cluster_id = dict()
        self.cluster_to_ele = dict()
        if data is None:
            return
        if not isinstance(data, (dict, list)):
            raise TypeError(f"Only list or dict allowed, but got {type(data)}")
        elif isinstance(data, list):
            self._from_set_list(data)
        elif isinstance(data, dict):
            self._from_dict(data)

    def __repr__(self):
        return str(self.cluster_to_ele)

    def __getitem__(self, key):
        if key in self.ele_to_cluster_id:
            cluster = self.cluster_to_ele[self.ele_to_cluster_id[key]]
            other_members = cluster.difference({key})
            if len(other_members) == 1:
                return next(iter(other_members))
            return other_members
        raise KeyError

    def __setitem__(self, key, value):
        raise TypeError("'Clusters' does not support item assignment use .add()")

    def add(
        self,
        new_entry: Union[Tuple[str, str], Set[str]],
    ):
        if not isinstance(new_entry, (tuple, set)):
            raise TypeError(f"Expected tuple or set, but got {type(new_entry)}")
        elif isinstance(new_entry, tuple):
            if len(new_entry) > 2:
                raise TypeError(
                    "Only tuple of len == 2 is allowed, but got {len(new_entry)}"
                )
            if new_entry[1] in self.ele_to_cluster_id:
                raise KeyError(f"{new_entry} already present, please use .update()")
            # add element to existing cluster
            elif new_entry[0] in self.ele_to_cluster_id:
                cluster_id = self.ele_to_cluster_id[new_entry[0]]
                self.ele_to_cluster_id[new_entry[1]] = cluster_id
                self.cluster_to_ele[cluster_id].add(new_entry[1])
                return
            # both elements do not exist yet -> handle as set
            new_entry = {new_entry[0], new_entry[1]}
        if not len(new_entry.intersection(self.ele_to_cluster_id.keys())) == 0:
            raise ValueError(
                "Set contains already present entries, please use .update()"
            )
        else:
            cluster_id = max(self.cluster_to_ele.keys()) + 1
            self.cluster_to_ele[cluster_id] = set()
            for e in new_entry:
                self.ele_to_cluster_id[e] = cluster_id
                self.cluster_to_ele[cluster_id].add(e)

    def remove(self, entry: str):
        cluster_id = self.ele_to_cluster_id[entry]
        del self.ele_to_cluster_id[entry]
        cluster = self.cluster_to_ele[cluster_id]
        if len(cluster) == 2:
            for member in cluster:
                if member != entry:
                    del self.ele_to_cluster_id[member]
            del self.cluster_to_ele[cluster_id]
        else:
            self.cluster_to_ele[cluster_id].remove(entry)

    def __eq__(self, other):
        if isinstance(other, Clusters):
            return (self.cluster_to_ele == other.cluster_to_ele) and (
                self.ele_to_cluster_id == other.ele_to_cluster_id
            )
        return False

    def __size__(self):
        return len(self.cluster_to_ele)

    def size(self):
        return self.__size__()
