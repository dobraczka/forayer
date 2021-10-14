"""Test word embedding module."""
import os

import pytest
from forayer.transformation.word_embedding import _EMBEDDING_INFO, AttributeVectorizer

_EMBEDDING_INFO["glove"] = (
    "https://speicherwolke.uni-leipzig.de/index.php/s/TyAaQtsJ8C9enDY/download",
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


def test_no_multiple_downloads(make_sure_test_embeddings_are_removed, capsys):
    av = AttributeVectorizer(embedding_type="glove")
    captured = capsys.readouterr()
    assert "Downloading glove embeddings to data/word_embeddings/glove" in captured.out
    assert not av._download_embeddings_if_needed()
    av = AttributeVectorizer(embedding_type="glove")
    captured = capsys.readouterr()
    assert "Downloading glove embeddings " not in captured.out


def test_attribute_vectorizer_non_existing_path():
    non_existing_path = "/test/nonexisting/"
    with pytest.raises(ValueError, match=non_existing_path):
        AttributeVectorizer(vectors_path=non_existing_path)
