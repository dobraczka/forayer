"""module containing knowledge graph class."""
from __future__ import annotations

import random
import warnings
from collections import defaultdict
from itertools import chain
from typing import Any, Dict, Iterable, List, Set, Union

from forayer.transformation.word_embedding import AttributeVectorizer
from forayer.utils.dict_help import dict_merge, nested_ddict2dict
from forayer.utils.random_help import random_generator
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
                and self.rel == other.rel
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

        Creates a subgraph with the wanted entities. Contains only relationships
        between wanted entities. Entities without attributes (possibly not contained
        in self.entities) and relationships that point outside the subgraph are added
        as entities without attributes to the result KG's entities.

        Parameters
        ----------
        wanted: Iterable[str]
            Ids of wanted entities.

        Returns
        -------
        KG
            subgraph with only wanted entities

        Examples
        --------
        >>> from forayer.knowledge_graph import KG
        >>> entities = {"e1": {"a": 1}, {"e2": {"a": 3}}
        >>> rel = {"e1": {"e2": "rel", "e3": "rel"}}
        >>> kg = KG(entities,rel)
        >>> kg.subgraph(["e1","e3"])
        KG(entities={'e1': {'a': 1}, 'e3': {}}, rel={'e1': {'e3': 'rel'}}, name=None)
        """
        wanted_entities = {
            ent_id: attr_dict
            for ent_id, attr_dict in self.entities.items()
            if ent_id in wanted
        }
        wanted_rel = defaultdict(dict)
        entities_in_rel = set()
        for ent_id, right_rel_dict in self.rel.items():
            if ent_id in wanted:
                for right_ent_id, rel_dict in right_rel_dict.items():
                    if right_ent_id in wanted:
                        entities_in_rel.add(ent_id)
                        entities_in_rel.add(right_ent_id)
                        wanted_rel[ent_id][right_ent_id] = rel_dict
        # add entities without attributes, that only show up in relationships
        # that point outside the subgraph and therefore were missed
        for w in wanted:
            if (w not in wanted_entities and w not in wanted_rel) and (
                w in self.entities or w in self.rel or w in self._inv_rel
            ):
                wanted_entities[w] = {}
        return KG(
            entities=wanted_entities, rel=nested_ddict2dict(wanted_rel), name=self.name
        )

    def add_entity(self, e_id: str, e_attr: Dict, overwrite: bool = False):
        """Add an entity to the knowledge graph.

        Parameters
        ----------
        e_id : str
            Id of the entity you want to add.
        e_attr : Dict
            Attributes of the entity you want to add.
        overwrite : bool
            If true, overwrite existing

        Raises
        ------
        ValueError
            If entity id is already present.
        """
        if e_id in self.entities and not overwrite:
            raise ValueError(f"{e_id} already exists: {self.entities[e_id]}")
        self.entities[e_id] = e_attr

    def remove_entity(self, e_id: str):
        """Remove the entity with the id.

        Parameters
        ----------
        e_id : str
            Id of entity you want to remove.

        Raises
        ------
        KeyError
            If no entity with this id exists
        """
        del self.entities[e_id]
        if e_id in self.rel:
            del self.rel[e_id]
        if e_id in self._inv_rel:
            for other_id in self._inv_rel[e_id]:
                del self.rel[other_id][e_id]
                if len(self.rel[other_id]) == 0:
                    del self.rel[other_id]
            del self._inv_rel[e_id]

    def _add_inv_rel(self, target, source):
        if target not in self._inv_rel:
            self._inv_rel[target] = {source}
        else:
            if source not in self._inv_rel[target]:
                current_value = self._inv_rel[target]
                if not isinstance(current_value, set):
                    current_value = {current_value}
                current_value.add(source)
                self._inv_rel[target] = current_value

    def add_rel(self, source: str, target: str, value, overwrite: bool = False) -> bool:
        """Add relationhip with value.

        Parameters
        ----------
        source : str
            Entity id of source.
        target : str
            Entity id of target.
        value
            Value of relation, e.g. relation name.
        overwrite : bool
            If true, overwrites existing values for already present
            relationship, else appends the value to existing.

        Returns
        -------
        bool
            True if new information was added, else false.
        """
        if (
            source in self.rel
            and target in self.rel[source]
            and value == self.rel[source][target]
        ):
            return False
        elif source not in self.rel:
            self.rel[source] = {target: value}
            self._add_inv_rel(target, source)
        elif target not in self.rel[source]:
            self.rel[source][target] = value
            self._add_inv_rel(target, source)
        else:  # new value for existing rel
            if overwrite:
                self.rel[source][target] = value
            else:
                current_value = self.rel[source][target]
                if not isinstance(current_value, list):
                    current_value = [current_value]
                current_value.append(value)
                self.rel[source][target] = current_value
        return True

    def remove_rel(self, source: str, target: str, value=None):
        """Remove relationship or relationship value.

        Parameters
        ----------
        source : str
            Entity id of source.
        target : str
            Entity id of target.
        value
            If provided: remove only this specific value.

        Raises
        ------
        KeyError
            If relationship does not exist
        ValueError
            If value does not exist in relationship
        """
        if value is not None:
            current_value = self.rel[source][target]
            value_not_found_msg = (
                f"Cannot remove {value} from {source} -> {target}, because it is not"
                f" present in {current_value}"
            )
            if isinstance(current_value, set):
                if value not in current_value:
                    raise ValueError(value_not_found_msg)
                current_value.remove(value)
                if len(current_value) == 1:
                    current_value = next(iter(current_value))
                self.rel[source][target] = current_value
                return True
            else:
                if value != current_value:
                    raise ValueError(value_not_found_msg)
                # here we can simply remove the relationship
        del self.rel[source][target]
        if len(self.rel[source]) == 0:
            del self.rel[source]
        self._inv_rel[target].remove(source)
        if len(self._inv_rel[target]) == 0:
            del self._inv_rel[target]

    def sample(self, n: int, seed: Union[int, random.Random] = None) -> KG:
        """Return a sample of the knowledge graph with n entities.

        Parameters
        ----------
        n : int
            Number of entities to return.
        seed : Union[int, random.Random]
            Seed for randomness or seeded random.Random object.
            Default is None.

        Returns
        -------
        KG
            Knowledge graph with n entities.

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
        r_gen = random_generator(seed)
        sampled_e_ids = r_gen.sample(self.entities.keys(), n)
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

    def __contains__(self, key):
        # some datasets have entities without attributes that
        # only show up in the relations
        if key in self.entities or key in self.rel or key in self._inv_rel:
            return True
        return False

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

    @property
    def entity_ids(self) -> Set[str]:
        """Return ids of all entities.

        Returns
        -------
        Set[str]
            Ids of all entities.
        """
        return (
            set(self.entities.keys())
            .union(set(self.rel.keys()))
            .union(set(self._inv_rel.keys()))
        )

    @property
    def attribute_names(self) -> Set[str]:
        """Return all attribute names.

        Returns
        -------
        Set[str]
            Attribute names as set.
        """
        # get list of sets of attribute dict keys
        # and flatten into one set using chain
        return set(chain(*[set(k.keys()) for k in self.entities.values()]))

    @property
    def relation_names(self) -> Set[str]:
        """Return all relation names.

        Returns
        -------
        Set[str]
            Relation names as set.
        """
        rel_names = set()
        for _, target_rel_dict in self.rel.items():
            for _, rel_dict in target_rel_dict.items():
                if isinstance(rel_dict, str):
                    rel_names.add(rel_dict)
                elif isinstance(rel_dict, dict):
                    probably_name = list(rel_dict.keys())
                    if len(probably_name) == 1:
                        rel_names.add(probably_name[0])
        return rel_names

    def _rel_signatures(self):
        all_rels = set()
        for left, right_dict in self.rel.items():
            for right, rel_values in right_dict.items():
                if isinstance(rel_values, list):
                    for rels in rel_values:
                        if isinstance(rels, dict):
                            for inner_rel_names in rels.keys():
                                all_rels.add(left + right + str(inner_rel_names))
                        else:
                            all_rels.add(left + right + str(rels))
                elif isinstance(rel_values, dict):
                    for inner_rel_names in rel_values.keys():
                        all_rels.add(left + right + str(inner_rel_names))
                else:
                    all_rels.add(left + right + str(rel_values))
        return all_rels

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
        num_rel = len(self._rel_signatures())
        name = "KG" if self.name is None else self.name
        return (
            f"{name}: (# entities: {len(self)}, # entities_with_rel: {num_ent_rel}, #"
            f" rel: {num_rel}, # entities_with_attributes: {num_ent}, #"
            f" attributes: {num_attr_name}, # attr_values: {num_attr_values})"
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

        >>> from rdflib.namespace import FOAF
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

    def __add__(self, other):
        merged_entities = dict_merge(self.entities, other.entities)
        merged_rel = dict_merge(self.rel, other.rel)
        return KG(entities=merged_entities, rel=merged_rel)

    def __len__(self):
        # some datasets have entities without attributes that
        # only show up in the relations
        return len(
            set(self.entities)
            .union(set(self.rel.keys()))
            .union(set(self._inv_rel.keys()))
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

        Examples
        --------
        >>> from forayer.knowledge_graph import AttributeEmbeddedKG
        >>> from forayer.datasets import OpenEADataset
        >>> dw15kv1 = OpenEADataset(ds_pair="D_W",size="15K",version=1)
        >>> from forayer.transformation.word_embedding import AttributeVectorizer

        For demonstration we take a sample

        >>> dbpedia = dw15kv1.er_task.kgs["DBpedia"].sample(1000)

        Initialize the Vectorizer with the pre-trained embeddings

        >>> vectorizer = AttributeVectorizer(embedding_type="fasttext")

        If you have them downloaded already you can also supply the path

        >>> vectorizer = AttributeVectorizer(embedding_type="fasttext",
                vectors_path=f"somepath/fasttext/wiki.simple.bin")

        Then create a knowledge graphs with embedded attribute tokens

        >>> dbp_embedded = AttributeEmbeddedKG.from_kg(dbpedia, vectorizer=vectorizer)
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
