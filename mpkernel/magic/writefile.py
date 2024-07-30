import os
from io import BytesIO

from ..kernel import MpKernel
from ..remote_ops import makedirs
from . import arg, cell_magic


def fput(kernel: MpKernel, data, remote_path: str, chunk_size=256):
    buf = BytesIO(data)
    makedirs(kernel, os.path.dirname(remote_path))
    kernel.exec_remote(f"_f=open('{remote_path}','wb');_w=_f.write")
    while True:
        data = buf.read(chunk_size)
        if not data:
            break
        kernel.exec_remote(f"_w({repr(data)})")
    kernel.exec_remote("_f.close()")


@arg(
    "-a", "--append", action="store_true", help="Append to file. Default is overwrite."
)
@arg(
    "-r",
    "--remote",
    action="store_true",
    help="Write to remote. Default is to write to host.",
)
@arg("path", help="file path")
@cell_magic
def writefile(kernel: MpKernel, args, code):
    """Write cell contents to file
    Example:
        %%writefile sample.py
        print("Hello, world!")

        %%writefile -r sample.py
        print("Hello from MicroPython")
    """
    if args.remote:
        fput(kernel, code.encode(), args.path)
    else:
        path = os.path.expanduser(args.path)
        path = os.path.expandvars(path)
        with open(path, "a" if args.append else "w") as f:
            f.write(code)
