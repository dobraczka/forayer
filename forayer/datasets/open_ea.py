"""OpenEA dataset class."""
import os

import pystow
from forayer.datasets.base_dataset import ForayerDataset
from forayer.input_output.from_to_open_ea import from_openea
from forayer.knowledge_graph import ERTask


class OpenEADataset(ForayerDataset):
    """The OpenEA datasets contain entity resolution tasks with samples from popular knowledge graphs.

    Several different tasks are available with snippets from DBpedia, Wikidata and YAGO.
    Different sizes refer to the number of entities in the respective graphs (15K or 100K).
    For each setting two versions are available, where version 1 has lower connectivity
    in the graph compared to version 2.

    More information can be found at the respective `github repository <https://github.com/nju-websoft/OpenEA>`_ and
    the benchmark publication: Sun et al (2020) `A Benchmarking Study of Embedding-based Entity Alignment for Knowledge Graphs`, *VLDB* <http://www.vldb.org/pvldb/vol13/p2326-sun.pdf>
    """

    __DOWNLOAD_URL = (
        "https://www.dropbox.com/s/xfehqm4pcd9yw0v/OpenEA_dataset_v2.0.zip?dl=1"
    )

    def __init__(
        self,
        ds_pair: str = "D_W",
        size: str = "15K",
        version: int = 1,
        force: bool = False,
    ):
        """Initialize an OpenEA dataset pair.

        Parameters
        ----------
        ds_pair : str
            name of ds pair (either "D_W" or "D_Y")
        size : str
            size of the task (either "15K" or "100K")
        version : int
            version of task (either 1 or 2)
        force : bool
            if true ignores cache
        """
        self.ds_pair = ds_pair
        self.size = size
        self.version = version
        name = f"{ds_pair}_{size}_V{version}"
        super().__init__(
            name=name,
            cache_path=pystow.join("forayer", "cache", name=f"OpenEA_{name}.pkl"),
            force=force,
        )

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"(ds_pair={self.ds_pair}, size={self.size},"
            f" version={self.version},{self.er_task})"
        )

    def _load(self) -> ERTask:
        """Load :class:`ERTask` object from raw files.

        Returns
        -------
        ERTask
            The er task created from the files
        """
        path = os.path.join("OpenEA_dataset_v2.0", self.name)
        return from_openea(path=path, url=self.__class__.__DOWNLOAD_URL)
