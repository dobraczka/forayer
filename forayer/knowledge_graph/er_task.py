from __future__ import annotations
from typing import TYPE_CHECKING, List

# avoid circular imports see: https://www.stefaanlippens.net/circular-imports-type-hints-python.html
if TYPE_CHECKING:

    from forayer.knowledge_graph import KG, ClusterHelper


class ERTask:
    def __init__(self, kgs: List[KG], clusters: ClusterHelper = None):
        kgs_dict = {}
        for cur_id, k in enumerate(kgs):
            if k.name is None:
                k.name = str(cur_id)
            kgs_dict[k.name] = k
        self.kgs = kgs_dict
        self.clusters = clusters
        self.__inv_attr = None

    def inverse_attr_dict(self):
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
