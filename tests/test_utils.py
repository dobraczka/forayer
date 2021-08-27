from forayer.utils.dict_help import dict_merge


def test_dict_merge():
    entities = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
    }
    entities2 = {"e4": {"a2": "another"}}

    e_expected = {
        "e1": {"a1": "first entity", "a2": 123},
        "e2": {"a1": "second ent"},
        "e3": {"a2": 124},
        "e4": {"a2": "another"},
    }
    assert dict_merge(entities, entities2) == e_expected
    rel = {"e1": {"e3": "somerelation"}}
    rel2 = {"e4": {"e1": "hello"}}
    r_expected = {"e1": {"e3": "somerelation"}, "e4": {"e1": "hello"}}
    assert dict_merge(rel, rel2) == r_expected
