"""module containing knowledge graph class."""
from __future__ import annotations

import itertools
import warnings
from collections.abc import MutableMapping
from pprint import pprint
from typing import Any, Dict, List, Set, Union

from forayer.transformation.word_embedding import AttributeVectorizer
from tqdm import tqdm


class KG:
    """KG class holding entities and their attributes and relations between entities."""

    def __init__(
        self,
        entities: Dict[Any, Dict[Any, Any]],
        rel: Dict[Any, Dict[Any, Any]] = None,
        name: str = None,
    ):
        """Initialize a KG object.

        Parameters
        ----------
        entities : Dict[Any, Dict[Any, Any]]
            entity information with entity ids as keys and a attribute dictionaries as values
            attribute dictionaries have attribute id as key and attribute value as dict value
        rel : Dict[Any, Dict[Any, Any]]
            relation triples with one entity as key, value is dict with other entity as key
            and relation id as value
        name : str, optional
            name of the kg, default is None

        Examples
        --------
        >>> entities = {
            "e1": {"a1": "first entity", "a2": 123},
            "e2": {"a1": "second ent"},
            "e3": {"a2": 124},
        }
        >>> relations = {"e1": {"e3": "somerelation"}}
        >>> kg = KG(entities, relations, "mykg")
        """
        self.entities = entities
        self.rel = rel
        inv_rel = {}
        for left_ent, right_ent_rel in rel.items():
            for right_ent, _ in right_ent_rel.items():
                if right_ent not in inv_rel:
                    inv_rel[right_ent] = set()
                inv_rel[right_ent].add(left_ent)
        self._inv_rel = inv_rel
        self.name = name

    def search(self, query, attr=None, exact=False):
        """Search for entities with specific attribute value.

        Parameters
        ----------
        query
            attribute value that is searched for
        attr : Union[str,List]
            only look in specific attribute(s)
        exact : bool
            if True only consider exact matches

        Examples
        --------
        >>> from forayer.knowledge_graph import KG
        >>> entities = {
                "e1": {"a1": "first entity", "a2": 123},
                "e2": {"a1": "second ent"},
                "e3": {"a2": 124},
            }
        >>> kg = KG(entities)
        >>> kg.search("first")
        {'e1': {'a1': 'first entity', 'a2': 123}}
        >>> kg.search("first", exact=True)
        {}
        >>> kg.search("first", attr="a2")
        {}
        """
        query = str(query)
        if attr is not None and not isinstance(attr, list):
            attr = [attr]
        result = {}
        for ent_id, attr_dict in self.entities.items():
            if attr is not None:
                filtered_attr_dict = {k: v for k, v in attr_dict.items() if k in attr}
            else:
                filtered_attr_dict = attr_dict
            if exact:
                if query in filtered_attr_dict.values():
                    result[ent_id] = attr_dict
            else:
                for _, value in filtered_attr_dict.items():
                    if query in str(value):
                        result[ent_id] = attr_dict
        return result

    def take(self, n: int) -> Dict[Any, Dict[Any, Any]]:
        """Return n entities.

        Iterates over entity dictionary and returns dictionary
        with the first n entities that come up during iteration.

        Parameters
        ----------
        n : int
            number of entities to return

        Returns
        -------
        Dict[Any, Dict[Any, Any]]
            n entities from knowledge graph

        Examples
        --------
        >>> from forayer.knowledge_graph import KG
        >>> entities = {
                "e1": {"a1": "first entity", "a2": 123},
                "e2": {"a1": "second ent"},
                "e3": {"a2": 124},
            }
        >>> kg = KG(entities)
        >>> kg.take(2)
        {'e1': {'a1': 'first entity', 'a2': 123}, 'e2': {'a1': 'second ent'}}
        """
        return {
            ent_id: attr_dict
            for ent_id, attr_dict in itertools.islice(self.entities.items(), n)
        }

    def __getitem__(self, key: Union[str, List[str]]) -> Dict[Any, Any]:
        """Return entity/entities with key(s).

        For a single key returns attributes of entity and is basically syntactic
        sugar for self.entities[key].
        For multiple keys, return a sub-dict of entities with the given ids.

        Parameters
        ----------
        key: Union[str, List[str]]
            entity id(s)

        Returns
        -------
        Dict[Any,Dict[Any,Any]]
            attributes of entity
        """
        if isinstance(key, list):
            return {e_id: self.entities[e_id] for e_id in key}
        return self.entities[key]

    def __setitem__(self, key, value):
        """Not implemented."""
        raise NotImplementedError

    def __repr__(self):
        return pprint(vars(self))

    def neighbors(
        self, entity_id: str, only_id: bool = False
    ) -> Union[Set[str], Dict[Any, Dict[Any, Any]]]:
        """Get neighbors of an entity.

        Parameters
        ----------
        entity_id: str
            The id of entity of which we want the neighbors.
        only_id: bool
            If true only ids are returned

        Returns
        -------
        neighbors: Union[Set[str], Dict[Any, Dict[Any,Any]]]
            entity dict of neighbors, if only_id is true returns neighbor ids as set
        """
        try:
            n_to_right = set(self.rel[entity_id].keys())
        except KeyError:
            n_to_right = set()
        try:
            n_to_left = self._inv_rel[entity_id]
        except KeyError:
            n_to_left = set()
        result_ids = n_to_right.union(n_to_left)
        if only_id:
            return result_ids
        return self[list(result_ids)]

    def info(self) -> str:
        """Print general information about this object.

        Returns
        -------
        str
            information about number of entities, attributes and values
        """
        num_ent = len(self.entities.keys())
        num_attr_name = len(self.entities.values())
        num_attr_values = len(
            {
                attr_value
                for _, attr_dict in self.entities.items()
                for _, attr_value in attr_dict.items()
            }
        )
        num_ent_rel = len(set(self.rel.keys()).union(set(self._inv_rel.keys())))
        name = "KG" if self.name is None else self.name
        return (
            f"{name}: (# entities_with_rel: {num_ent_rel}, # rel: {len(self.rel)}, #"
            f" entities_with_attributes: {num_ent}, # attributes: {num_attr_name}, #"
            f" attr_values: {num_attr_values})"
        )


class AttributeEmbeddedKG(KG):
    """KG class holding entities and their embedded attributes as well as relations between entities."""

    def __init__(
        self,
        entities: Dict[Any, Dict[Any, Any]],
        rel: Dict[Any, Dict[Any, Any]],
        vectorizer: AttributeVectorizer,
        name: str = None,
    ):
        """Initialize an attribute embeded KG object.

        Calculates the attribute embeddings given a tokenizer and vectorizer.

        Parameters
        ----------
        entities : Dict[Any, Dict[Any, Any]]
            entity information with entity ids as keys and a attribute dictionaries as values
            attribute dictionaries have attribute id as key and attribute value as dict value
        rel : Dict[Any, Dict[Any, Any]]
            relation triples with one entity as key, value is dict with other entity as key
            and relation id as value
        vectorizer: AttributeVectorizer
            an attribute vectorizer to use for retrieving the embeddings
        name : str, optional
            name of the kg, default is None
        """
        self.vectorizer = vectorizer
        self.vectorizer.reset_token_count()
        attr_embedded_entities = {
            e_id: self.vectorizer.vectorize_entity_attributes(ent_attr)
            for e_id, ent_attr in tqdm(entities.items(), desc="Vectorizing attributes")
        }
        if self.vectorizer.ignored_tokens > 0:
            warnings.warn(
                f"{self.vectorizer.ignored_tokens}/{self.vectorizer.seen_tokens} tokens"
                " have no pre-trained embedding and were replaced by np.NaN"
            )
        self._ignored = self.vectorizer.ignored_tokens
        self._seen = self.vectorizer.seen_tokens
        super(AttributeEmbeddedKG, self).__init__(attr_embedded_entities, rel, name)

    def __repr__(self):
        return self.info()

    def info(self) -> str:
        """Print general information about this object.

        Returns
        -------
        str
            information about number of entities, attributes and embedded attributes
        """
        num_ent = len(self.entities.keys())
        num_attr_name = len(self.entities.values())
        num_ent_rel = len(set(self.rel.keys()).union(set(self._inv_rel.keys())))
        name = "KG" if self.name is None else self.name
        return (
            f"{name}: (# entities_with_rel: {num_ent_rel}, # rel: {len(self.rel)}, #"
            f" entities_with_attributes: {num_ent}, # attributes: {num_attr_name},"
            f" {self._ignored}/{self._seen} tokens"
            " have no pre-trained embedding and were replaced by np.NaN)"
        )

    @classmethod
    def from_kg(cls, kg: KG, vectorizer: AttributeVectorizer) -> AttributeEmbeddedKG:
        """Initialize an attribute embedded KG object from a knowledge graph object.

        Parameters
        ----------
        kg : KG
            a pre-populated knowledge graph
        vectorizer: AttributeVectorizer
            an attribute vectorizer to use for retrieving the embeddings

        Returns
        -------
        AttributeEmbeddedKG
            the given KG with vectorized attribute values
        """
        return AttributeEmbeddedKG(
            entities=kg.entities, rel=kg.rel, vectorizer=vectorizer, name=kg.name
        )
