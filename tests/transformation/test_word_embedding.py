"""Test word embedding module."""
import logging
import os

import pytest

from forayer.transformation.word_embedding import _EMBEDDING_INFO, AttributeVectorizer

_EMBEDDING_INFO["glove"] = (
    "https://cloud.scadsai.uni-leipzig.de/index.php/s/7xkBke3iGRgPYDd/download/GloveTest.zip",
    "GloveTest.zip",
    "testglove.txt",
)


def _remove_test_embeddings():
    file_path = os.path.join("data/word_embeddings/glove/", _EMBEDDING_INFO["glove"][2])
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def make_sure_test_embeddings_are_removed():
    _remove_test_embeddings()
    yield
    _remove_test_embeddings()


def test_no_multiple_downloads(make_sure_test_embeddings_are_removed, caplog):
    caplog.set_level(logging.INFO)
    av = AttributeVectorizer(embedding_type="glove")
    assert "Downloading glove embeddings to data/word_embeddings/glove" in caplog.text
    assert not av._download_embeddings_if_needed()
    caplog.clear()
    av = AttributeVectorizer(embedding_type="glove")
    assert "Downloading glove embeddings " not in caplog.text


def test_attribute_vectorizer_non_existing_path():
    non_existing_path = "/test/nonexisting/"
    with pytest.raises(ValueError, match=non_existing_path):
        AttributeVectorizer(vectors_path=non_existing_path)
