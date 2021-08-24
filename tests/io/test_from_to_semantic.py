import datetime
import os
import pathlib

from forayer.io.from_to_semantic import load_from_triples


def test_from_semantic():
    test_data_folder = os.path.join(
        pathlib.Path(__file__).parent.parent.resolve(), "test_data"
    )
    kg = load_from_triples(os.path.join(test_data_folder, "test.ttl"))
    assert kg["http://example.org/#spiderman"][
        "http://xmlns.com/foaf/0.1/birthday"
    ] == datetime.date(year=1963, month=8, day=10)
    assert kg["http://example.org/#spiderman"]["http://xmlns.com/foaf/0.1/name"] == {
        "Spiderman",
        "Человек-паук",
    }
    assert (
        kg.rel["http://example.org/#spiderman"]["http://xmlns.com/foaf/0.1/Person"]
        == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    )
    assert (
        kg.rel["http://example.org/#green-goblin"]["http://xmlns.com/foaf/0.1/Person"]
        == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    )
    assert (
        kg["http://example.org/#green-goblin"]["http://xmlns.com/foaf/0.1/name"]
        == "Green Goblin"
    )
    assert (
        kg.rel["http://example.org/#spiderman"]["http://example.org/#green-goblin"]
        == "http://www.perceive.net/schemas/relationship/enemyOf"
    )
    assert kg["http://example.org/#spiderman"]["http://xmlns.com/foaf/0.1/age"] == 27
    assert (
        kg.rel["http://example.org/#green-goblin"]["http://example.org/#spiderman"]
        == "http://www.perceive.net/schemas/relationship/enemyOf"
    )
