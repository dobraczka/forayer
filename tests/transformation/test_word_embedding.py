"""Test word embedding module."""
import pytest
from forayer.transformation.word_embedding import AttributeVectorizer


def test_attribute_vectorizer_non_existing_path():
    non_existing_path = "/test/nonexisting/"
    with pytest.raises(ValueError, match=non_existing_path):
        AttributeVectorizer(vectors_path=non_existing_path)
