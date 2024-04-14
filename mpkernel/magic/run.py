import sys

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "path",
    nargs=1,
    help="Path to file to run",
)
@line_magic
def run_magic(kernel: MpKernel, args):
    """Execute code from file on remote device"""
    filename = args.path[0]
    try:
        with open(filename, "rb") as f:
            buf = f.read()
        kernel.exec_remote(buf)
    except OSError:
        print(f"could not read file '{filename}'", file=sys.stderr)
