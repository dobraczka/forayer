import forayer.transformation.word_embedding
import numpy as np
import pytest
from forayer.knowledge_graph import KG, AttributeEmbeddedKG
from forayer.transformation.word_embedding import AttributeVectorizer
from numpy.testing import assert_array_equal


def test_basic():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
    }
    kg = KG(entities, {"e1": {"e3": "somerelation"}})
    assert kg["e1"] == kg.entities["e1"]

    assert kg.take(3) == kg.entities


def test_neighbors():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
    }
    kg = KG(entities, {"e1": {"e3": "somerelation"}})

    assert kg.neighbors("e1") == {"e3"}
    assert kg.neighbors("e3") == {"e1"}

    kg_dual_rel = KG(
        entities, {"e1": {"e3": "somerelation"}, "e3": {"e1": "other_rel"}}
    )

    assert kg_dual_rel.neighbors("e1") == {"e3"}
    assert kg_dual_rel.neighbors("e3") == {"e1"}


def test_attribute_embedded(tmpdir):
    entities = {
        "e1": {"a1": "first entity", "a2": "test"},
        "e2": {"a1": "second"},
        "e3": {"a2": "third"},
    }
    kg = KG(entities, {"e1": {"e3": "somerelation"}}, "testkg")

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


def test_attribute_embedded_with_missing_embeddings(tmpdir):
    entities = {
        "e1": {"a1": "first entity", "a2": "test"},
        "e2": {"a1": "second"},
        "e3": {"a2": "third"},
    }
    kg = KG(entities, {"e1": {"e3": "somerelation"}}, "testkg")

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

    assert str(class_initialized_a_kg) == class_initialized_a_kg.info
