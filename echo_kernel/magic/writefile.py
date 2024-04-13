import os

from ..kernel import EchoKernel
from . import arg, cell_magic


@arg(
    "-a", "--append", action="store_true", help="Append to file. Default is overwrite."
)
@arg("path", help="file path")
@cell_magic
def writefile(kernel: EchoKernel, args, code):
    """Write cell contents to file
    Example:
        %%writefile sample.py
        print("Hello, world!")
    """
    path = os.path.expanduser(args.path)
    path = os.path.expandvars(path)
    print(f"Writing {path}")
    with open(path, "a" if args.append else "w") as f:
        f.write(code)
