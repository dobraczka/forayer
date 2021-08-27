from __future__ import annotations

from functools import reduce
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, List

from forayer.utils.dict_help import dict_merge

# avoid circular imports see: https://www.stefaanlippens.net/circular-imports-type-hints-python.html
if TYPE_CHECKING:

    from forayer.knowledge_graph import KG, ClusterHelper


class ERTask:
    """Class to model entity resolution task on knowledge graphs.

    Attributes
    ----------
    kgs_dict: Dict[str, KG]
        dictionary of given KGs, with KG names as keys
        KGs without names have their list index as key
    clusters: ClusterHelper
        known entity clusters
    """

    def __init__(self, kgs: List[KG], clusters: ClusterHelper = None):
        """Initialize an ERTask object.

        Parameters
        ----------
        kgs : List[KG]
            list of KGs that are to be integrated
        clusters : ClusterHelper
            known entity clusters
        """
        kgs_dict = {}
        for cur_id, k in enumerate(kgs):
            if k.name is None:
                k.name = str(cur_id)
            kgs_dict[k.name] = k
        self.kgs = kgs_dict
        self.clusters = clusters
        self.__inv_attr = None

    def __repr__(self):
        kg_info = "{" + ",".join([k.info() for _, k in self.kgs.items()]) + "}"
        return self.__class__.__name__ + f"({kg_info},{str(self.clusters.info())})"

    def __getitem__(self, key):
        return self.kgs[key]

    def sample(self, n: int, unmatched: int = None):
        sample_clusters = self.clusters.sample(n)
        print("len(sample_clusters)=%s" % (len(sample_clusters)))
        entity_ids = list(sample_clusters.elements.keys())
        print("len(entity_ids)=%s" % (len(entity_ids)))
        if unmatched is not None:
            unm_ent = set()
            for cand in self.clusters.elements.keys():
                if len(unm_ent) == unmatched:
                    break
                if cand not in self.clusters:
                    unmatched.add(cand)
                elif cand not in entity_ids:
                    cand_links = self.clusters.links(cand, always_return_set=True)
                    if not any(c in entity_ids or c in unm_ent for c in cand_links):
                        unm_ent.add(cand)
            entity_ids.extend(list(unm_ent))
        print("len(entity_ids)=%s" % (len(entity_ids)))
        for _, k in self.kgs.items():
            print(f"total: {len(k)}")
        sampled_kgs = [k.subgraph(entity_ids) for k_name, k in self.kgs.items()]
        for k in sampled_kgs:
            print(len(k))
        return ERTask(kgs=sampled_kgs, clusters=sample_clusters)

    def all_entities(self) -> Dict[str, Dict]:
        """Return the entities of all KGs in a single dict"""
        return reduce(dict_merge, [k.entities for k in self.kgs.values()])

    def without_match(self):
        return [
            e
            for e in chain(*[list(k.entities.keys()) for k in self.kgs.values()])
            if e not in self.clusters
        ]

    def __len__(self):
        return sum([len(k) for k in self.kgs.values()])

    def inverse_attr_dict(self) -> Dict[Any, Dict[str, str]]:
        """Create an attributes dictionary with unique attribute values as key.

        Returns
        -------
        Dict[Any, Dict[str,str]]
            inverse attribute dict
        """
        if self.__inv_attr is None:
            attr_to_kg_to_attr_name_to_ent = {}
            for kg_name, kg in self.kgs.items():
                for ent_id, ent_attr_dict in kg.entities.items():
                    for attr_name, attr_value in ent_attr_dict.items():
                        if attr_value not in attr_to_kg_to_attr_name_to_ent:
                            attr_to_kg_to_attr_name_to_ent[attr_value] = {}
                        if kg_name not in attr_to_kg_to_attr_name_to_ent[attr_value]:
                            attr_to_kg_to_attr_name_to_ent[attr_value][kg_name] = {}
                        if (
                            attr_name
                            not in attr_to_kg_to_attr_name_to_ent[attr_value][kg_name]
                        ):
                            attr_to_kg_to_attr_name_to_ent[attr_value][kg_name][
                                attr_name
                            ] = []
                        attr_to_kg_to_attr_name_to_ent[attr_value][kg_name][
                            attr_name
                        ].append(ent_id)
            self.__inv_attr = attr_to_kg_to_attr_name_to_ent
        return self.__inv_attr
