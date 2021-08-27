"""Helper for more complicated dict functions."""
from collections import defaultdict


# see https://stackoverflow.com/a/30921635
def nested_ddict():
    """Create a nested defaultdict."""
    return defaultdict(nested_ddict)


# see https://stackoverflow.com/a/30921635
def nested_ddict2dict(d):
    """Cast a nested defaultdict to dict."""
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = nested_ddict2dict(v)
    return dict(d)


def _merge(a, b, path=None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if (
                not (isinstance(a[key], dict) and isinstance(b[key], dict))
                or a[key] == b[key]
            ):
                raise Exception("Conflict at %s" % ".".join(path + [str(key)]))
            elif isinstance(a[key], dict) and isinstance(b[key], dict):
                dict_merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
        else:
            a[key] = b[key]
    return a


# see https://stackoverflow.com/a/7205107
def dict_merge(a, b):
    """Merge a and b.

    Parameters
    ----------
    a
        One dictionary that will be merged
    b
        Other dictionary that will be merged
    """
    return _merge(dict(a), b)
