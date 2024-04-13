import argparse
import shlex
from collections import OrderedDict
from functools import wraps

# dictionaries of handlers name --> (method, descripion)
LINE_MAGIC = OrderedDict()
CELL_MAGIC = OrderedDict()


# @cell_magic decorator, use last (after all @arg's)
def cell_magic(fn):
    # function that is called when invoking the magic
    @wraps(fn)
    def wrapped(kernel, line, body):
        args = None
        try:
            # parse line
            args = wrapped.parser.parse_args(shlex.split(line))  # type: ignore
        except SystemExit:
            pass
        if args:
            fn(kernel, args, body)

    # extract magic name and docstring
    name = fn.__name__.rsplit("_")[0]
    doc = (fn.__doc__ or "").split("\n", 1)
    if len(doc) < 2:
        doc.append("")

    # construct the parser
    wrapped.parser = argparse.ArgumentParser(  # type: ignore
        prog="%%" + name,
        description=doc[0],
        epilog=doc[1],
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(
            prog, max_help_position=22, width=80
        ),
    )

    # add to dict
    CELL_MAGIC[name] = (wrapped, doc[0])
    return wrapped


# @line_magic decorator, use last (after all @arg's)
def line_magic(fn):
    # function that is called when invoking the magic
    @wraps(fn)
    def wrapped(kernel, line):
        args = None
        try:
            # parse line
            args = wrapped.parser.parse_args(shlex.split(line))  # type: ignore
        except SystemExit:
            pass
        if args:
            fn(kernel, args)

    # extract magic name and docstring
    name = fn.__name__.rsplit("_")[0]
    doc = (fn.__doc__ or "").split("\n", 1)
    if len(doc) < 2:
        doc.append("")

    # construct the parser
    wrapped.parser = argparse.ArgumentParser(  # type: ignore
        prog="%" + name,
        description=doc[0],
        epilog=doc[1],
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(
            prog, max_help_position=22, width=80
        ),
    )
    # formatter_class=argparse.RawDescriptionHelpFormatter)

    # add to dict
    LINE_MAGIC[name] = (wrapped, doc[0])
    return wrapped


# @arg decorator (may be repeated)
def arg(*args, **kwargs):
    # add argument to the parser that was construction by @line_magic
    def wrap(fn):
        fn.parser.add_argument(*args, **kwargs)
        return fn

    return wrap
