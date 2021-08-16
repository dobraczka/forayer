"""base classes for datasets."""
import os
import shutil
from abc import abstractmethod
from zipfile import ZipFile

import wget


class Dataset:
    """base class for dataset classes."""

    def __init__(self, download_folder: str):
        """Initialize a dataset object.

        Downloads and unzips necessary data

        Parameters
        ----------
        download_folder : str
            folder path where raw data is stored
        """
        self.download_folder = download_folder
        self.download_and_unzip()

    @abstractmethod
    def load(self):
        """Load and prepare the dataset object from the downloaded files."""
        pass

    def _get_download_dir(self):
        if self.download_folder.endswith(os.sep):
            return os.path.split(os.path.split(self.download_folder)[0])[0]
        return os.path.split(self.download_folder)[0]

    def download_and_unzip(self):
        """Download and unzip files to download folder if needed."""
        if not os.path.exists(self.download_folder):
            target_dir = self._get_download_dir()
            # make sure download dir is present
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            # get zip file paths
            zip_dirs = [os.path.join(target_dir, z) for z in self.__class__._zip_names]
            print(f"Downloading {self.__class__.__name__} datasets to {zip_dirs}")
            for zip_dir, dl_url, zip_name in zip(
                zip_dirs, self.__class__._download_urls, self.__class__._zip_names
            ):
                wget.download(dl_url, zip_dir)
                with ZipFile(zip_dir, "r") as zip_obj:
                    zip_obj.extractall(target_dir)
                    # move to wanted dir
                    # TODO what if top level folder is not named like the zip file
                    unpacked_zip = os.path.join(
                        target_dir, zip_name.replace(".zip", "")
                    )
                    file_names = os.listdir(unpacked_zip)
                    for file_name in file_names:
                        shutil.move(os.path.join(unpacked_zip, file_name), target_dir)
                # cleanup
                os.remove(zip_dir)
                os.rmdir(unpacked_zip)
