from forayer.input_output.from_to_open_ea import from_openea


def test_simple_remote_open_ea():
    url = "https://cloud.scadsai.uni-leipzig.de/index.php/s/D5XLC4gSDyaESRe"
    ertask = from_openea("TestData", kg_names=[0, 1], url=url)
    assert ertask[0]["e1"]["p1"] == "test"
    assert ertask[1]["e2"]["p1"] == "test2"
    assert ertask[0].rel["e1"]["e3"] == "rel"
    assert ertask[1].rel["e2"]["e4"] == "rel"
    assert ertask.clusters.elements["e1"] == ertask.clusters.elements["e2"]
    assert ertask.clusters.elements["e3"] == ertask.clusters.elements["e4"]
