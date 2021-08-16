"""module containing knowledge graph class."""
from typing import Any, Dict, Set

from forayer.transformation.word_embedding import AttributeVectorizer


class KG:
    """KG class holding entities and their attributes and relations between entities."""

    def __init__(
        self,
        entities: Dict[Any, Dict[Any, Any]],
        rel: Dict[Any, Dict[Any, Any]],
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

    def neighbors(self, entity_id) -> Set[str]:
        """Get neighbors of an entity.

        Parameters
        ----------
        entity_id :
            id of entity of which we want the neighbors

        Returns
        -------
        neighbors: set
            neighbor ids as set
        """
        try:
            n_to_right = set(self.rel[entity_id].keys())
        except KeyError:
            n_to_right = set()
        try:
            n_to_left = self._inv_rel[entity_id]
        except KeyError:
            n_to_left = set()
        return n_to_right.union(n_to_left)


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
        attr_embedded_entities = {
            e_id: self.vectorizer.vectorize_entity_attributes(ent_attr)
            for e_id, ent_attr in entities.items()
        }
        super(AttributeEmbeddedKG, self).__init__(attr_embedded_entities, rel, name)

    @classmethod
    def from_kg(cls, kg: KG, vectorizer: AttributeVectorizer):
        """Initialize an attribute embedded KG object from a knowledge graph object.

        Parameters
        ----------
        kg : KG
            a pre-populated knowledge graph
        vectorizer: AttributeVectorizer
            an attribute vectorizer to use for retrieving the embeddings
        """
        return AttributeEmbeddedKG(
            entities=kg.entities, rel=kg.rel, vectorizer=vectorizer, name=kg.name
        )
