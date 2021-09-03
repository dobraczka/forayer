from __future__ import annotations

import random
from functools import reduce
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, List, Set, Union

from forayer.utils.dict_help import dict_merge
from forayer.utils.random_help import random_generator

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

    def sample(
        self, n: int, seed: Union[int, random.Random] = None, unmatched: int = None
    ):
        """Create a sample of the ERTask.

        Takes n clusters and creates the respective subgraphs.
        If unmatched is provided adds a number of entities without
        match to the subgraphs.

        Parameters
        ----------
        n : int
            Number of clusters.
        seed : Union[int, random.Random]
            Seed for randomness or seeded random.Random object.
            Default is None.
        unmatched : int
            Number of unmatched entities to include. Default is None.

        Returns
        -------
        ERTask
            downsampled ERTask

        Examples
        --------
        >>> from forayer.datasets import OpenEADataset
        >>> ds = OpenEADataset(ds_pair="D_W",size="15K",version=1)
        >>> ds.er_task.sample(n=10,unmatched=20)
        ERTask({DBpedia: (# entities: 26, # entities_with_rel: 0, # rel: 0, # entities_with_attributes: 26, # attributes: 26, # attr_values: 89),Wikidata: (# entities: 14, # entities_with_rel: 0, # rel: 0, # entities_with_attributes: 14, # attributes: 14, # attr_values: 102)},ClusterHelper(# elements:20, # clusters:10))

            You can use a seed to control reproducibility


        >>> ds.er_task.sample(n=10,seed=13,unmatched=20)
        ERTask({DBpedia: (# entities: 26, # entities_with_rel: 0, # rel: 0, # entities_with_attributes: 26, # attributes: 26, # attr_values: 93),Wikidata: (# entities: 14, # entities_with_rel: 0, # rel: 0, # entities_with_attributes: 14, # attributes: 14, # attr_values: 179)},ClusterHelper(# elements:20, # clusters:10))
        """
        r_gen = random_generator(seed)
        sample_clusters = self.clusters.sample(n, seed=r_gen)
        entity_ids = list(sample_clusters.elements.keys())
        if unmatched is not None:
            unm_ent = set()
            no_match_entities = self.without_match()
            if len(no_match_entities) >= n:
                unm_ent = r_gen.sample(no_match_entities)
            else:
                unm_ent = no_match_entities
                for cand in self.entity_ids:
                    if len(unm_ent) == unmatched:
                        break
                    if cand not in self.clusters:
                        unmatched.add(cand)
                    elif cand not in entity_ids:
                        cand_links = self.clusters.links(cand, always_return_set=True)
                        if not any(c in entity_ids or c in unm_ent for c in cand_links):
                            unm_ent.append(cand)
            entity_ids.extend(list(unm_ent))
        for _, k in self.kgs.items():
            sampled_kgs = [k.subgraph(entity_ids) for k_name, k in self.kgs.items()]
        return ERTask(kgs=sampled_kgs, clusters=sample_clusters)

    @property
    def entity_ids(self) -> Set[str]:
        """Return entity ids of all knowledge graphs.

        Returns
        -------
        Set[str]
            Entity ids of all knowledge graphs as set.
        """
        return set(chain(*[k.entity_ids for k in self.kgs.values()]))

    def all_entities(self, ignore_only_relational: bool = False) -> Dict[str, Dict]:
        """Return all entities.

        Parameters
        ----------
        ignore_only_relational : bool
            If True, ignores entities that only show up in the relations
            (and not in the entities with attributes)
        Returns
        -------
        Dict[str, Dict]
            all entities
        """
        all_attr_ent = reduce(dict_merge, [k.entities for k in self.kgs.values()])
        if not ignore_only_relational:
            for kg in self.kgs.values():
                for e in kg.rel:
                    if e not in all_attr_ent:
                        all_attr_ent[e] = {}
                for e in kg._inv_rel:
                    if e not in all_attr_ent:
                        all_attr_ent[e] = {}
        return all_attr_ent

    def without_match(self):
        """Return ids of entities without matches in given gold standard."""
        return [e for e in self.entity_ids if e not in self.clusters]

    def __len__(self):
        return sum([len(k) for k in self.kgs.values()])

    def __eq__(self, other):
        if isinstance(other, ERTask):
            return self.clusters == other.clusters and self.kgs == other.kgs
        return False

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
