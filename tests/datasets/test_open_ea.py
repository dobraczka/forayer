from typing import List

import pytest

from forayer.datasets import OpenEADataset
from forayer.knowledge_graph import KG


def triples(kg: KG, attributes=True) -> List:
    all_trip = []
    trip_dict = kg.entities if attributes else kg.rel
    for key, inner_dict in trip_dict.items():
        for inner_key, v in inner_dict.items():
            if isinstance(v, set):
                for v_i in v:
                    all_trip.append((key, inner_key, v_i))
            else:
                all_trip.append((key, inner_key, v))
    return all_trip


@pytest.mark.slow
def test_open_ea_dataset():
    dw15kv1 = OpenEADataset(
        ds_pair="D_W",
        size="15K",
        version=1,
        force=True,
    )
    # assert high-level statistics
    dbpedia = dw15kv1.er_task["DBpedia"]
    wikidata = dw15kv1.er_task["Wikidata"]
    assert len(dbpedia) == 15000
    assert len(wikidata) == 15000

    assert len(triples(dbpedia)) == 52134
    assert len(triples(wikidata)) == 138246

    assert len(triples(dbpedia, attributes=False)) == 38265
    assert len(triples(wikidata, attributes=False)) == 42746

    assert len(dbpedia.attribute_names) == 341
    assert len(wikidata.attribute_names) == 649

    assert len(dbpedia.relation_names) == 248
    assert len(wikidata.relation_names) == 169

    # assert some specific entity
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

    # test multi-value literals
    assert len(dw15kv1.er_task["DBpedia"]["http://dbpedia.org/resource/E348417"]) == 1

    assert set(
        dw15kv1.er_task["DBpedia"]["http://dbpedia.org/resource/E348417"][
            "http://dbpedia.org/ontology/firstAppearance"
        ]
    ) == {
        '\\"Winter Is Coming\\" (2011)',
        "A Game of Thrones (1996)",
        "Television:",
        "Novel:",
    }

    # test print working
    assert str(dw15kv1)
