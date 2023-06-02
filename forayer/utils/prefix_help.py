from typing import Any, Dict, Generator, Tuple

import pystow


class PrefixHelper:
    """Use shortened prefix via prefix.cc or given prefix mappings."""
    def __init__(
        self, prefix_mapping: Dict[str, str] = None, only_use_given: bool = False
    ):
        prefix_mapping = prefix_mapping or {}
        if only_use_given:
            self.prefix_mapping = prefix_mapping
        else:
            predefined = {}
            for _, row in pystow.ensure_csv("forayer", url="http://prefix.cc/popular/all.file.csv", read_csv_kwargs=dict(header=None, names=["prefix", "full"], sep=",")).iterrows():
                # prefixes are sorted by popularity
                # we want the most popular ones
                if row["full"] not in predefined:
                    predefined[row["full"]] = row["prefix"]
            self.prefix_mapping = {**predefined, **prefix_mapping}

    def _replace_if_possible(self, value: str) -> str:
        if "/" in value:
            possible_prefixable, postfix = value.rsplit("/", 1)
            possible_prefixable += "/"
            if possible_prefixable in self.prefix_mapping:
                return self.prefix_mapping[possible_prefixable] + ":" + postfix
        return value

    def replacement_triple_generator(
        self, entity_info: Dict
    ) -> Generator[Tuple[Any, Any, Any], None, None]:
        """Returns a generator of triples with shortened prefixes.

        :param entity_info: Entity info to shorten prefixes
        :return: A generator of triples with shortened prefixes
        """
        for e_name, e_attr_dict in entity_info.items():
            e_name = self._replace_if_possible(e_name)
            for attr_name, attr_val in e_attr_dict.items():
                attr_name = self._replace_if_possible(attr_name)
                yield e_name, self.prefix_mapping.get(attr_name, attr_name), attr_val

