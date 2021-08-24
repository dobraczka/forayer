"""base classes for datasets."""
import os
import pathlib
from typing import List, Tuple
from zipfile import ZipFile

import wget


class Dataset:
    """Base class for dataset classes."""

    DS_NAME = ""


class RemoteDataset(Dataset):
    """Base class for dataset with remote files."""

    def __init__(self, download_urls: List[Tuple[str, str]], data_folder: str = None):
        """Initialize a dataset object.

        Parameters
        ----------
        download_urls : List[Tuples(str, str)]
            List of tuples with (url, target_file_name)
        data_folder : str
            folder path where raw data is stored.
            If NONE, stores in "forayer_root/data/self.__class__.DS_NAME"
        """
        # get root of project
        project_root = pathlib.Path(__file__).parent.parent.parent.resolve()
        self.data_folder = (
            data_folder
            if data_folder is not None
            else os.path.join(project_root, "data", self.__class__.DS_NAME)
        )
        self.download_urls = download_urls

    def download(self, check_files=False) -> bool:
        """Download files and create download dir if necessary.

        check_files: bool
            Instead of checking for data_folder check individual files.

        Returns
        -------
        bool
            True if download was needed.
        """
        if not os.path.exists(self.data_folder):
            print(
                f"Downloading {self.__class__.__name__} datasets to {self.data_folder}"
            )
            os.makedirs(self.data_folder)
            for url, target in self.download_urls:
                target_file_path = os.path.join(self.data_folder, target)
                print(f"Downloading {url} to {target_file_path}")
                wget.download(url, target_file_path)
            return True
        elif check_files:
            at_least_one = False
            for url, target in self.download_urls:
                target_file_path = os.path.join(self.data_folder, target)
                if not os.path.exists(target_file_path):
                    at_least_one = True
                    print(f"Downloading {url} to {target_file_path}")
                    wget.download(url, target_file_path)
            if at_least_one:
                return True
        return False


class ZipDataset(RemoteDataset):
    """Base class for datasets that have remote zipped raw files."""

    def __init__(self, data_folder: str, download_urls: List[Tuple[str, str]]):
        """Initialize a dataset object.

        Downloads and unzips necessary data

        Parameters
        ----------
        download_urls : List[Tuples(str, str)]
            List of tuples with (url, target_file_name)
        data_folder : str
            folder path where raw data is stored
        """
        super(ZipDataset, self).__init__(download_urls, data_folder)

    def download_and_unzip(self) -> bool:
        """Download and unzip files to download folder if needed.

        Returns
        -------
        bool
            True if download was needed.
        """
        if self.download():
            # get zip file paths
            for _, zip_name in self.download_urls:
                zip_dir = os.path.join(self.data_folder, zip_name)
                with ZipFile(zip_dir, "r") as zip_obj:
                    zip_obj.extractall(self.data_folder)
                # cleanup
                os.remove(zip_dir)
            return True
        return False
