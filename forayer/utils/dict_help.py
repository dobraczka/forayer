"""Helper for more complicated dict functions."""
# see https://stackoverflow.com/a/30921635
from collections import defaultdict


def nested_ddict():
    """Create a nested defaultdict."""
    return defaultdict(nested_ddict)


def nested_ddict2dict(d):
    """Cast a nested defaultdict to dict."""
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = nested_ddict2dict(v)
    return dict(d)
