import forayer.transformation.word_embedding
import numpy as np
import pytest
from forayer.knowledge_graph import KG, AttributeEmbeddedKG
from forayer.transformation.word_embedding import AttributeVectorizer
from numpy.testing import assert_array_equal
from rdflib import Literal, URIRef
from rdflib.namespace import FOAF


@pytest.fixture
def simple_kg_entites_rel_123():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
    }
    rel = {"e1": {"e3": "somerelation"}}
    return entities, rel


@pytest.fixture
def kg_first_second_third():
    entities = {
        "e1": {"a1": "first entity", "a2": "test"},
        "e2": {"a1": "second"},
        "e3": {"a2": "third"},
    }
    return entities, {"e1": {"e3": "somerelation"}}


def test_basic(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    kg = KG(entities=entities, rel=rel, name="kg1")
    assert kg["e1"] == kg.entities["e1"]
    assert kg[["e1", "e2", "e3"]] == entities

    kg2 = KG(entities=entities, rel=rel, name="kg1")
    assert kg == kg2


def test_subgraph():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
        "e4": {"a1": 24},
    }
    rel = {"e1": {"e3": "somerelation"}, "e4": {"e3": "somerelation", "e1": "test"}}
    kg = KG(entities=entities, rel=rel)
    sub = kg.subgraph(wanted=["e3", "e4"])
    assert sub.entities == {"e3": {"a2": 124}, "e4": {"a1": 24}}
    assert sub.rel == {"e4": {"e3": "somerelation"}}

    # test entities that only show up in rel
    entities2 = {"e1": {"a": 1}, "e2": {"a": 3}}
    rel2 = {"e1": {"e2": "rel", "e3": "rel"}}
    kg2 = KG(entities=entities2, rel=rel2, name="kg")
    assert kg2.subgraph(["e1", "e3"]) == KG(
        entities={"e1": {"a": 1}, "e3": {}}, rel={"e1": {"e3": "rel"}}, name="kg"
    )


def test_sample():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
        "e4": {"a1": 24},
    }
    rel = {
        "e1": {"e2": "somerelation", "e3": "somerelation"},
        "e4": {"e3": "somerelation", "e1": "test"},
    }
    kg = KG(entities=entities, rel=rel)
    one = kg.sample(1)
    assert len(one) == 1
    assert one.rel == {}

    two = kg.sample(2)
    assert len(two) == 2
    if set(two.entities.keys()) == {"e1", "e2"}:
        assert two.entities == {
            "e1": {"a1": "first entity", "a2": 123},
            "e2": {"a1": "second ent"},
        }
        assert two.rel == {"e1": {"e2": "somerelation"}}


def test_neighbors(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    kg = KG(entities, rel)

    assert kg.neighbors("e1", only_id=True) == {"e3"}
    assert kg.neighbors("e3", only_id=True) == {"e1"}

    kg_dual_rel = KG(
        entities, {"e1": {"e3": "somerelation"}, "e3": {"e1": "other_rel"}}
    )

    assert kg_dual_rel.neighbors("e1", only_id=True) == {"e3"}
    assert kg_dual_rel.neighbors("e3", only_id=True) == {"e1"}


def test_search(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    e1 = ("e1", entities["e1"])
    e2 = ("e2", entities["e2"])
    e3 = ("e3", entities["e3"])
    entities = {e_id: val for e_id, val in [e1, e2, e3]}
    kg = KG(entities, rel)

    assert kg.search("first entity") == {e1[0]: e1[1]}
    assert kg.search("first entity", attr=None) == {e1[0]: e1[1]}
    assert kg.search("first entity", attr="a1") == {e1[0]: e1[1]}
    assert kg.search("first entity", attr=["a1"]) == {e1[0]: e1[1]}

    assert kg.search("first") == {e1[0]: e1[1]}
    assert kg.search("first", attr=None) == {e1[0]: e1[1]}
    assert kg.search("first", attr="a1") == {e1[0]: e1[1]}
    assert kg.search("first", attr=["a1"]) == {e1[0]: e1[1]}
    assert kg.search("first", attr="a2") == {}

    assert kg.search("first", exact=True) == {}

    assert kg.search(124, attr="a2") == {e3[0]: e3[1]}
    assert kg.search("124", attr="a2") == {e3[0]: e3[1]}
    assert kg.search("124") == {e3[0]: e3[1]}
    assert kg.search(124) == {e3[0]: e3[1]}


def test_with_attr(simple_kg_entites_rel_123):
    entities, _ = simple_kg_entites_rel_123
    kg = KG(entities)
    assert kg.with_attr("a1") == {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
    }
    assert kg.with_attr("a3") == {}


def test_attribute_embedded(tmpdir, kg_first_second_third):
    entities, rel = kg_first_second_third
    kg = KG(entities, rel, "testkg")

    # use toy embeddings to speed up test and lower traffic
    forayer.transformation.word_embedding._EMBEDDING_INFO["glove"] = (
        "https://speicherwolke.uni-leipzig.de/index.php/s/yRmkFEXHX6J4cQL/download",
        "test_embeddings.zip",
        "glove.6B.300d.txt",
    )

    vectorizer = AttributeVectorizer(
        embedding_type="glove", default_download_dir=tmpdir
    )
    class_initialized_a_kg = AttributeEmbeddedKG.from_kg(kg, vectorizer=vectorizer)
    normal_initialized_a_kg = AttributeEmbeddedKG(
        entities=kg.entities, rel=kg.rel, vectorizer=vectorizer, name=kg.name
    )

    assert (
        entities["e1"].keys()
        == class_initialized_a_kg.entities["e1"].keys()
        == normal_initialized_a_kg.entities["e1"].keys()
    )
    assert (
        entities["e2"].keys()
        == class_initialized_a_kg.entities["e2"].keys()
        == normal_initialized_a_kg.entities["e2"].keys()
    )
    assert (
        entities["e3"].keys()
        == class_initialized_a_kg.entities["e3"].keys()
        == normal_initialized_a_kg.entities["e3"].keys()
    )

    assert len(class_initialized_a_kg.entities["e1"]["a1"]) == 2
    assert len(normal_initialized_a_kg.entities["e1"]["a1"]) == 2

    assert class_initialized_a_kg.entities["e1"]["a1"][0].shape == (300,)
    assert_array_equal(
        class_initialized_a_kg.entities["e1"]["a1"][0],
        normal_initialized_a_kg.entities["e1"]["a1"][0],
    )

    assert class_initialized_a_kg["e1"] == class_initialized_a_kg.entities["e1"]


EXPECTED_WARNING = (
    "1/5 tokens have no pre-trained embedding and were replaced by np.NaN"
)


def test_attribute_embedded_with_missing_embeddings(tmpdir, kg_first_second_third):
    entities, rel = kg_first_second_third
    kg = KG(entities, rel, "testkg")

    # use toy embeddings to speed up test and lower traffic
    forayer.transformation.word_embedding._EMBEDDING_INFO["glove"] = (
        "https://speicherwolke.uni-leipzig.de/index.php/s/nzGo7GeDxyzFpfN/download",
        "test_embeddings_with_missing.zip",  # "first" does not have an embedding
        "glove.6B.300d.txt",
    )

    vectorizer = AttributeVectorizer(
        embedding_type="glove", default_download_dir=tmpdir
    )
    with pytest.warns(UserWarning, match=EXPECTED_WARNING):
        class_initialized_a_kg = AttributeEmbeddedKG.from_kg(kg, vectorizer=vectorizer)
    with pytest.warns(UserWarning, match=EXPECTED_WARNING):
        normal_initialized_a_kg = AttributeEmbeddedKG(
            entities=kg.entities, rel=kg.rel, vectorizer=vectorizer, name=kg.name
        )

    assert (
        entities["e1"].keys()
        == class_initialized_a_kg.entities["e1"].keys()
        == normal_initialized_a_kg.entities["e1"].keys()
    )
    assert (
        entities["e2"].keys()
        == class_initialized_a_kg.entities["e2"].keys()
        == normal_initialized_a_kg.entities["e2"].keys()
    )
    assert (
        entities["e3"].keys()
        == class_initialized_a_kg.entities["e3"].keys()
        == normal_initialized_a_kg.entities["e3"].keys()
    )

    assert len(class_initialized_a_kg.entities["e1"]["a1"]) == 2
    assert len(normal_initialized_a_kg.entities["e1"]["a1"]) == 2
    assert np.isnan(class_initialized_a_kg.entities["e1"]["a1"][0])
    assert np.isnan(normal_initialized_a_kg.entities["e1"]["a1"][0])

    assert class_initialized_a_kg.entities["e1"]["a1"][1].shape == (300,)
    assert_array_equal(
        class_initialized_a_kg.entities["e1"]["a1"][1],
        normal_initialized_a_kg.entities["e1"]["a1"][1],
    )

    assert (
        str(class_initialized_a_kg)
        == "testkg: (# entities_with_rel: 2, # rel: 1, # entities_with_attributes: 3, #"
        " attributes: 3, "
        + EXPECTED_WARNING
        + ")"
    )

    assert str(class_initialized_a_kg) == class_initialized_a_kg.info()


EXPECTED_TRIPLES = {
    (URIRef("e1"), URIRef("a1"), Literal("first entity")),
    (URIRef("e1"), URIRef("a2"), Literal(123)),
    (URIRef("e2"), URIRef("a1"), Literal("second ent")),
    (URIRef("e3"), URIRef("a2"), Literal(124)),
    (URIRef("e3"), URIRef("a2"), Literal("1223")),
    (URIRef("e1"), URIRef("somerelation"), URIRef("e3")),
}

EXPECTED_TRIPLES_PREFIXED = {
    (
        URIRef("https://test.org/e1"),
        URIRef("http://xmlns.com/foaf/0.1/name"),
        Literal("first entity"),
    ),
    (URIRef("https://test.org/e1"), URIRef("https://testattr.org/"), Literal(123)),
    (
        URIRef("https://test.org/e2"),
        URIRef("http://xmlns.com/foaf/0.1/name"),
        Literal("second ent"),
    ),
    (URIRef("https://test.org/e3"), URIRef("https://testattr.org/"), Literal(124)),
    (URIRef("https://test.org/e3"), URIRef("https://testattr.org/"), Literal("1223")),
    (
        URIRef("https://test.org/e1"),
        URIRef("http://xmlns.com/foaf/0.1/knows"),
        URIRef("https://test.org/e3"),
    ),
}


def test_to_rdflib():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": {124, "1223"}},
    }
    kg = KG(entities, {"e1": {"e3": "somerelation"}})
    rdf_g = kg.to_rdflib()

    assert set(rdf_g) == set(EXPECTED_TRIPLES)

    rdf_g = kg.to_rdflib(
        prefix="https://test.org/",
        attr_mapping={
            "a1": FOAF.name,
            "a2": "https://testattr.org/",
            "somerelation": FOAF.knows,
        },
    )

    assert set(rdf_g) == set(EXPECTED_TRIPLES_PREFIXED)


def test_add_kgs(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    entities2 = {"e4": {"a2": "another"}}
    rel2 = {"e4": {"e1": "hello"}}
    kg1 = KG(entities=entities, rel=rel)
    kg2 = KG(entities=entities2, rel=rel2)

    e_expected = {
        "e1": entities["e1"],
        "e2": entities["e2"],
        "e3": entities["e3"],
        "e4": {"a2": "another"},
    }
    r_expected = {"e1": {"e3": "somerelation"}, "e4": {"e1": "hello"}}
    expected = KG(entities=e_expected, rel=r_expected)
    assert kg1 + kg2 == expected


def test_add_entity(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    kg1 = KG(entities=entities, rel=rel)
    with pytest.raises(ValueError):
        kg1.add_entity("e3", {"a2": 124})
    kg1.add_entity("e4", {"a1": "test"})
    assert kg1["e4"] == {"a1": "test"}


def test_remove_entity(simple_kg_entites_rel_123):
    entities, rel = simple_kg_entites_rel_123
    kg1 = KG(entities=entities, rel=rel)
    assert not kg1.remove_entity("e6")
    assert kg1.remove_entity("e3")
    assert not "e3" in kg1
