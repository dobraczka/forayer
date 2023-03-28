import pytest

from forayer.datasets import OAEIKGDataset


@pytest.mark.slow
def test_open_ea_dataset():
    ds = OAEIKGDataset(task="memoryalpha-memorybeta", force=True)

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
    # make sure print is working
    assert str(ds)
