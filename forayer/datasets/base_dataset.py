"""base classes for datasets."""
import os
from functools import wraps
from pathlib import Path
from typing import Union

from forayer.knowledge_graph import KG, ClusterHelper, ERTask
from pystow.cache import CachedPickle


class ForayerDataset:
    """Base class for dataset classes."""

    def __init__(
        self, name: str, cache_path: Union[str, Path, os.PathLike], force: bool
    ):
        """Initialize a forayer dataset.

        Parameters
        ----------
        name : str
            name of dataset
        cache_path : Union[str, Path, os.PathLike]
            path where pickle is/will be cached
        force : bool
            if true ignores the cache
        """
        self.name = name
        self.cache_path = cache_path
        self.force = force
        self.er_task = self.load_er_task()

    def load_er_task(self):
        """Load the ERtask via self._load() or from cache."""
        return CachedPickle(path=self.cache_path, force=self.force)(self._load)()

    def _load(self):
        raise NotImplementedError("Datasets must implement the _load() method!")
