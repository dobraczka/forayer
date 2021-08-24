import os
import pathlib

from forayer.datasets import OAEIKGDataset


def test_open_ea_dataset():
    test_data_folder = os.path.join(
        pathlib.Path(__file__).parent.parent.resolve(), "test_data"
    )
    ds = OAEIKGDataset(
        task="memoryalpha-memorybeta",
        data_folder=os.path.join(test_data_folder, "OAEI_KG_Track"),
    )

    assert (
        ds.er_task.kgs["memoryalpha"].entities[
            "http://dbkwik.webdatacommons.org/memory-alpha.wikia.com/resource/Verillian"
        ]["http://www.w3.org/2000/01/rdf-schema#label"]
        == "Verillian"
    )
    assert (
        ds.er_task.kgs["memorybeta"].entities[
            "http://dbkwik.webdatacommons.org/memory-beta.wikia.com/resource/Verillian"
        ]["http://www.w3.org/2000/01/rdf-schema#label"]
        == "Verillian"
    )

    assert (
        ds.er_task.clusters.elements[
            "http://dbkwik.webdatacommons.org/memory-alpha.wikia.com/resource/Verillian"
        ]
        == ds.er_task.clusters.elements[
            "http://dbkwik.webdatacommons.org/memory-beta.wikia.com/resource/Verillian"
        ]
    )
