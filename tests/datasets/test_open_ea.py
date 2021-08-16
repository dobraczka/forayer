from forayer.datasets import OpenEADataset


def test_open_ea_dataset():
    dw15kv1 = OpenEADataset(
        ds_pair="D_W",
        size="15K",
        version=1,
    )
    assert (
        dw15kv1.er_task.kgs["DBpedia"].entities["http://dbpedia.org/resource/E534644"][
            "http://dbpedia.org/ontology/imdbId"
        ]
        == "0044475"
    )
    assert (
        dw15kv1.er_task.kgs["DBpedia"].rel["http://dbpedia.org/resource/E534644"][
            "http://dbpedia.org/resource/E662096"
        ]
        == "http://dbpedia.org/ontology/distributor"
    )
    assert (
        dw15kv1.er_task.kgs["Wikidata"].entities[
            "http://www.wikidata.org/entity/Q3793661"
        ]["http://www.wikidata.org/entity/P345"]
        == "tt0044475"
    )
    assert (
        dw15kv1.er_task.kgs["Wikidata"].rel["http://www.wikidata.org/entity/Q6176218"][
            "http://www.wikidata.org/entity/Q145"
        ]
        == "http://www.wikidata.org/entity/P27"
    )

    assert (
        dw15kv1.er_task.clusters.elements["http://dbpedia.org/resource/E534644"]
        == dw15kv1.er_task.clusters.elements["http://www.wikidata.org/entity/Q3793661"]
    )
