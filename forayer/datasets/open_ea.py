"""OpenEA dataset class."""
import os

from forayer.datasets.base_dataset import ZipDataset
from forayer.input_output.from_to_open_ea import from_openea
from forayer.knowledge_graph import ERTask


class OpenEADataset(ZipDataset):
    """The OpenEA datasets contain entity resolution tasks with samples from popular knowledge graphs.

    Several different tasks are available with snippets from DBpedia, Wikidata and YAGO.
    Different sizes refer to the number of entities in the respective graphs (15K or 100K).
    For each setting two versions are available, where version 1 has lower connectivity
    in the graph compared to version 2.

    More information can be found at the respective `github repository <https://github.com/nju-websoft/OpenEA>`_ and
    the benchmark publication: Sun et al (2020) `A Benchmarking Study of Embedding-based Entity Alignment for Knowledge Graphs`, *VLDB* <http://www.vldb.org/pvldb/vol13/p2326-sun.pdf>
    """

    DS_NAME = "OpenEA"

    __DOWNLOAD_URLS = [
        (
            "https://www.dropbox.com/s/xfehqm4pcd9yw0v/OpenEA_dataset_v2.0.zip?dl=1",
            "OpenEA_dataset_v2.0.zip",
        )
    ]

    def __init__(
        self,
        ds_pair: str,
        size: str,
        version: int,
        data_folder: str = None,
    ):
        """Initialize an OpenEA dataset pair.

        Parameters
        ----------
        ds_pair : str
            name of ds pair (either "D-W" or "D-Y")
        size : str
            size of the task (either "15K" or "100K")
        version : int
            version of task (either 1 or 2)
        data_folder : str
            folder where raw files are stored or will be downloaded
        """
        super(OpenEADataset, self).__init__(
            data_folder=data_folder, download_urls=self.__class__.__DOWNLOAD_URLS
        )
        self.ds_pair = ds_pair
        self.size = size
        self.version = version
        self.download_and_unzip()
        self.er_task = self._load()

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"(ds_pair={self.ds_pair}, size={self.size}, version={self.version},"
            f" data_folder={self.data_folder}, {self.er_task})"
        )

    def _load(self) -> ERTask:
        """Load :class:`ERTask` object from raw files.

        Returns
        -------
        ERTask
            The er task created from the files
        """
        task_folder = os.path.join(
            self.data_folder,
            self.__class__.__DOWNLOAD_URLS[0][1].replace(".zip", ""),
            f"{self.ds_pair}_{self.size}_V{self.version}",
        )
        return from_openea(task_folder)
