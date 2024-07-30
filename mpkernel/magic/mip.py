from ..kernel import MpKernel
from ..mip import install
from . import arg, line_magic


@arg("-f", "--overwrite", action="store_true", help="overwrite existing files")
@arg("--mpy", action="store_true", help="install .mpy files (when available)")
@arg(
    "--target",
    default="./remote/lib",
    help="destination on the device",
)
@arg("--index", help="package index to use (defaults to micropython-lib)")
@arg(
    "packages",
    nargs="+",
    help="list package specifications, e.g. name, name@version, github:org/repo, github:org/repo@branch",
)
@arg("command", nargs=1, help="mip command (e.g. install)")
@line_magic
def mip_magic(kernel: MpKernel, args):
    """Install MicroPython packages on the local device.

    Important: unlike mpremote, this magic installs packages on the local device.
    Use %rsync or %fs cp to copy them to the remote device.

    Examples:
    %mip install abc argparse
    %mip install gzip@1.0.1
    """
    if args.command[0] != "install":
        print(f"Unknown command: {args.command[0]}")
    for package in args.packages:
        n = package.split("@")
        name, version = n if len(n) == 2 else (n[0], None)
        install(
            name,
            index=args.index,
            target=args.target,
            version=version,
            mpy=args.mpy,
            overwrite=args.overwrite,
        )
