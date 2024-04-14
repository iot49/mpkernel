import os

from ..kernel import MpKernel
from . import arg, line_magic


@arg("path", nargs="?", default="~", help="new working directory on host")
@line_magic
def cd_magic(kernel: MpKernel, args):
    """Change current working directory on host
    Expands ~ and shell variables."""
    path = os.path.expanduser(args.path)
    path = os.path.expandvars(path)
    if not os.path.isdir(path):
        raise ValueError(f"directory '{path}' does not exist")
    os.chdir(path)
    print(f"cwd = {os.getcwd()}")


@line_magic
def cwd_magic(kernel: MpKernel, args):
    """Print current working directory on host"""
    print(f"cwd = {os.getcwd()}")
