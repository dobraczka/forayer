import re
from typing import Any, Callable
from rdflib.plugins.parsers.ntriples import r_literal

def clean_attr_value(attr_value: Any):
    """Remove datatype and language tags

    :param attr_value: attribute value to clean
    """
    if isinstance(attr_value, list):
        return [clean_attr_value(inner_attr_value) for inner_attr_value in attr_value]
    elif isinstance(attr_value, str):
        match = r_literal.match(attr_value)
        if match is None:
            return attr_value
        else:
            return match.groups()[0]
    else:
        return attr_value
