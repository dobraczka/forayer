import sys
import warnings


def warning_formatter(msg, category, filename, lineno, line=None):
    """Format warning to only print filename, linenumber and message.

    Parameters
    ----------
    msg
        warning message
    category
        warning category
    filename
        filename of file where warning was raised
    lineno
        linenumber where warning was raised
    line
        line containing warning

    Returns
    -------
    str
        formatted warning message
    """
    return f"{filename}:L{lineno}: {msg}\n"


warnings.formatwarning = warning_formatter


if sys.version_info[1] > 7:
    from importlib.metadata import version  # pragma: no cover
else:
    from importlib_metadata import version  # pragma: no cover

__version__ = version(__package__)
