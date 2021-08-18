"""OpenEA dataset class."""
import os
import pathlib

from forayer.datasets.base_dataset import Dataset
from forayer.io.from_to_open_ea import from_openea
from forayer.knowledge_graph import ERTask


class OpenEADataset(Dataset):
    """Dataset class for OpenEA benchmark datasets."""

    _download_urls = [
        "https://www.dropbox.com/s/xfehqm4pcd9yw0v/OpenEA_dataset_v2.0.zip?dl=1"
    ]
    _zip_names = ["OpenEA_dataset_v2.0.zip"]

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
            name of ds pair
        size : str
            size of the task (either "15K" or "100K")
        version : int
            version of task (either 1 or 2)
        data_folder : str
            folder where raw files are stored or will be downloaded
        """
        self.ds_pair = ds_pair
        self.size = size
        self.version = version
        BASE = pathlib.Path(__file__).parent.parent.parent.resolve()
        self.data_folder = (
            data_folder
            if data_folder is not None
            else os.path.join(BASE, "data", "open_ea")
        )
        download_folder = os.path.join(
            self.data_folder, f"{self.ds_pair}_{self.size}_V{self.version}"
        )
        super(OpenEADataset, self).__init__(download_folder=download_folder)
        self.er_task = self.load()

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"(ds_pair={self.ds_pair}, size={self.size}, version={self.version},"
            f" data_folder={self.data_folder},"
            f" download_folder={self.download_folder}, {self.er_task})"
        )

    def load(self) -> ERTask:
        """Load :class:`ERTask` object from raw files.

        Returns
        -------
        ERTask
            The er task created from the files
        """
        return from_openea(self.download_folder)