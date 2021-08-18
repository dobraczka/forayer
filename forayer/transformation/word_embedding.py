"""Module concerned with utilizing word embeddings."""
import logging
import os
from typing import Any, Callable, Dict, List
from zipfile import ZipFile

import numpy as np
import wget
from gensim.models import KeyedVectors
from gensim.models.fasttext import load_facebook_model
from gensim.utils import tokenize

_EMBEDDING_INFO = {
    "fasttext": (
        "https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.simple.zip",
        "wiki.simple.zip",  # zip name
        "wiki.simple.bin",  # file containing wanted embeddings
    ),
    "glove": (
        "http://nlp.stanford.edu/data/glove.6B.zip",
        "glove.6B.zip",
        "glove.6B.300d.txt",
    ),
}


class AttributeVectorizer:
    """Vectorizer class to get attribute embeddings of entities with pre-trained embeddings.

    Attributes
    ----------
    tokenizer: Callable
        callable that tokenizes a string
    embedding_type: str
        type of pretrained embeddings
    vectors_path: str
        path to pre-trained embeddings
    wv: gensim.models.KeyedVectors
        word embeddings
    """

    def __init__(
        self,
        tokenizer: Callable = None,
        embedding_type: str = "glove",
        vectors_path: str = None,
        default_download_dir: str = None,
    ):
        """Initialize an AttributeVectorizer object and load the pre-trained embeddings.

        Parameters
        ----------
        tokenizer: Callable
            callable that tokenizes a string
        embedding_type: str
            type of pretrained embeddings
        vectors_path: str
            path to pre-trained embeddings
        default_download_dir: str
            directory where embeddings are downloaded if they are not present
            default is "./data/word_embeddings/"

        Raises
        ------
        TypeError
            if tokenizer is not callable
        ValueError
            if embedding_type is unknown or vectors_path does not exist
        """
        if tokenizer is None:
            self.tokenizer = tokenize
        else:
            if not hasattr(tokenizer, "___call__"):
                raise TypeError(
                    f"tokenizer should be a function, but was {type(tokenizer)}"
                )
            else:
                self.tokenizer = tokenizer
        embedding_type = embedding_type.lower()
        if embedding_type not in _EMBEDDING_INFO:
            raise ValueError(
                f"embedding_type has to be one of {set(_EMBEDDING_INFO.keys())}, not"
                f" {embedding_type}"
            )
        self.embedding_type = embedding_type
        if vectors_path is not None and not os.path.exists(vectors_path):
            raise ValueError(f"vectors_path: {self.vectors_path} does not exist")
        self.vectors_path = vectors_path
        self.default_download_dir = (
            default_download_dir
            if default_download_dir is not None
            else os.path.join("data", "word_embeddings")
        )
        self._download_embeddings_if_needed()
        self.wv = self._load_embeddings()
        self.vocab = {}
        self.seen_tokens = 0
        self.ignored_tokens = 0

    def reset_token_count(self):
        """Reset .seen_tokens and .ignored_tokens."""
        self.seen_tokens = 0
        self.ignored_tokens = 0

    def _download_embeddings_if_needed(self):
        if self.vectors_path is None:
            embeddings_dir = os.path.join(
                self.default_download_dir, self.embedding_type
            )
            if not os.path.exists(embeddings_dir):
                os.makedirs(embeddings_dir)
            dl_url, zip_name, embedding_file = _EMBEDDING_INFO[self.embedding_type]
            logging.info(
                f"Downloading {self.embedding_type} embeddings to {embeddings_dir}"
            )
            wget.download(dl_url, embeddings_dir)
            with ZipFile(os.path.join(embeddings_dir, zip_name), "r") as zip_obj:
                zip_obj.extractall(embeddings_dir)
            os.remove(os.path.join(embeddings_dir, zip_name))
            self.vectors_path = os.path.join(embeddings_dir, embedding_file)

    def _load_embeddings(self):
        logging.info("Loading word embeddings")
        if self.embedding_type == "fasttext":
            return load_facebook_model(self.vectors_path).wv
        try:
            return KeyedVectors.load_word2vec_format(self.vectors_path, binary=False)
        except ValueError:
            if self.embedding_type == "glove":
                wv = KeyedVectors.load_word2vec_format(
                    self.vectors_path, binary=False, no_header=True
                )
                return wv

    def vectorize(self, sentence: str) -> List[np.ndarray]:
        """Tokenize and vectorize a sentence with the given word embeddings.

        Parameters
        ----------
        sentence : str
            sentence to vectorize

        Returns
        -------
        vectorized: List[np.ndarray]
            List of token embeddings,

        Notes
        -----
        Ignores tokens that are not contained in the used embeddings
        Ignored tokens will be set to np.NaN
        """
        vectorized = []
        _number_of_tokens = 0  # initialize before in case loop is not executed
        for _number_of_tokens, word in enumerate(self.tokenizer(sentence), start=1):
            if word in self.wv:
                vectorized.append(self.wv[word])
            else:
                vectorized.append(np.NaN)
                self.ignored_tokens += 1
                logging.debug(f"Did not find embedding for {word}, ignoring")
        self.seen_tokens += _number_of_tokens
        return vectorized

    def vectorize_entity_attributes(
        self, attributes: Dict[Any, Any]
    ) -> Dict[Any, List[np.ndarray]]:
        """Tokenize and vectorize values of entity attributes.

        Parameters
        ----------
        attributes : Dict[Any, Any]
            dictionary of entity attributes with attribute names as keys

        Returns
        -------
        embedded_entity_attributes: Dict[Any, List[np.ndarray]]
            entity dicts with attribute values replaced with list of token embeddings
        """
        return {
            attr_name: self.vectorize(attr_value)
            for attr_name, attr_value in attributes.items()
        }
