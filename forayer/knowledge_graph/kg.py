"""module containing knowledge graph class."""
from __future__ import annotations

import itertools
import warnings
from collections import defaultdict
from pprint import pprint
from typing import Any, Dict, Iterable, List, Set, Union

from forayer.transformation.word_embedding import AttributeVectorizer
from rdflib import Graph, Literal, URIRef
from tqdm import tqdm


class KG:
    """KG class holding entities and their attributes and relations between entities."""

    def __init__(
        self,
        entities: Dict[str, Dict[Any, Any]],
        rel: Dict[str, Dict[str, Any]] = None,
        name: str = None,
    ):
        """Initialize a KG object.

        Parameters
        ----------
        entities : Dict[str, Dict[Any, Any]]
            entity information with entity ids as keys and a attribute dictionaries as values
            attribute dictionaries have attribute id as key and attribute value as dict value
        rel : Dict[str, Dict[str, Any]]
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
        if rel is not None:
            for left_ent, right_ent_rel in rel.items():
                for right_ent, _ in right_ent_rel.items():
                    if right_ent not in inv_rel:
                        inv_rel[right_ent] = set()
                    inv_rel[right_ent].add(left_ent)
        self._inv_rel = inv_rel
        self.name = name

    def __eq__(self, other):
        if isinstance(other, KG):
            return (
                self.entities == other.entities
                and self.rel == self.rel
                and self.name == other.name
            )
        return False

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

        Returns
        -------
        result: Dict[str, Dict[str, Any]]
            Entites that have attribute values that match the query.

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

    def with_attr(self, attr: str):
        """Search for entities with specific attribute.

        Parameters
        ----------
        attr: str
            Attribute name.

        Returns
        -------
        result: Dict[str, Dict[str, Any]]
            Entites that have the attribute.

        Examples
        --------
        >>> from forayer.knowledge_graph import KG
        >>> entities = {
                "e1": {"a1": "first entity", "a2": 123},
                "e2": {"a1": "second ent"},
                "e3": {"a2": 124},
            }
        >>> kg = KG(entities)
        >>> kg.with_attr("a1")
        {'e1': {'a1': 'first entity', 'a2': 123}, "e2": {"a1": "second ent"}}
        """
        return {
            ent_id: attr_dict
            for ent_id, attr_dict in self.entities.items()
            if attr in attr_dict
        }

    def subgraph(self, wanted: Iterable[str]):
        """Return a subgraph with only wanted entities.

        Parameters
        ----------
        wanted: Iterable[str]
            Ids of wanted entities.

        Returns
        -------
        KG
            subgraph with only wanted entities
        """
        sample_entities = {
            ent_id: attr_dict
            for ent_id, attr_dict in self.entities.items()
            if ent_id in wanted
        }
        sample_rel = defaultdict(dict)
        for ent_id, right_rel_dict in self.rel.items():
            if ent_id in sample_entities:
                for right_ent_id, rel_dict in right_rel_dict.items():
                    if right_ent_id in sample_entities:
                        sample_rel[ent_id][right_ent_id] = rel_dict
        return KG(entities=sample_entities, rel=sample_rel, name=self.name)

    def sample(self, n: int) -> Dict[Any, Dict[Any, Any]]:
        """Return a sample of the knowledge graph with n entities.

        Parameters
        ----------
        n : int
            number of entities to return

        Returns
        -------
        KG
            knowledge graph with n entities

        Examples
        --------
        >>> from forayer.knowledge_graph import KG
        >>> entities = {
                "e1": {"a1": "first entity", "a2": 123},
                "e2": {"a1": "second ent"},
                "e3": {"a2": 124},
            }
        >>> kg = KG(entities)
        >>> kg.sample(2)
        KG(entities={'e1': {'a1': 'first entity', 'a2': 123},
            'e2': {'a1': 'second ent'}},rel=None,name=None)
        """
        sampled_e_ids = list(itertools.islice(self.entities.keys(), n))
        return self.subgraph(sampled_e_ids)

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
        return f"KG(entities={self.entities}, rel={self.rel}, name={self.name})"

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

    def to_rdflib(self, prefix: str = "", attr_mapping: dict = None):
        """Transform to rdflib graph.

        Parameters
        ----------
        prefix : str
            Prefix to prepend to each entity id
        attr_mapping : dict
            Mapping of attribute names to URIs.
            Mapping values can be str or :class:`rdflib.term.URIRef`.
            This is also used to map relation predicates.

        Returns
        -------
        rdf_g
            rdflib Graph

        Examples
        --------
        >>> entities = {
            "e1": {"a1": "first entity", "a2": 123},
            "e2": {"a1": "second ent"},
            "e3": {"a2": {124, "1223"}},
        }
        >>> kg = KG(entities, {"e1": {"e3": "somerelation"}})
        >>> rdf_g = kg.to_rdflib()
        >>> from rdflib import URIRef
        >>> rdf_g.value(URIRef("e1"), URIRef("a1"))
        rdflib.term.Literal('first entity')

        You can use custom prefixes and rdflib namespaces or strings for mappings
        >>> my_prefix = "http://example.org/"
        >>> my_mapping = {"a1":FOAF.name, "a2":"http://example.org/attr"}
        >>> rdf_g = kg.to_rdflib(prefix=my_prefix,attr_mapping=my_mapping)
        >>> rdf_g.value(URIRef(my_prefix + "e1"), FOAF.name)
        rdflib.term.Literal('first entity')
        """

        def get_predicate(raw, attr_mapping):
            substitute = attr_mapping.get(raw, raw)
            if isinstance(substitute, URIRef):
                return substitute
            return URIRef(substitute)

        rdf_g = Graph()
        if attr_mapping is None:
            attr_mapping = {}
        for e_id, attr_dict in tqdm(
            self.entities.items(), desc="Transforming entities"
        ):
            for attr_name, attr_value in attr_dict.items():
                subject = URIRef(prefix + e_id)
                predicate = get_predicate(attr_name, attr_mapping)
                if isinstance(attr_value, (set, list)):
                    for inner_attr_val in attr_value:
                        object = Literal(inner_attr_val)
                        rdf_g.add((subject, predicate, object))
                else:
                    object = Literal(attr_value)
                    rdf_g.add((subject, predicate, object))
        for left_id, right_id_rel in self.rel.items():
            for right_id, rel in right_id_rel.items():
                subject = URIRef(prefix + left_id)
                predicate = get_predicate(rel, attr_mapping)
                object = URIRef(prefix + right_id)
                rdf_g.add((subject, predicate, object))
        return rdf_g

    def __len__(self):
        return len(self.entities)


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
