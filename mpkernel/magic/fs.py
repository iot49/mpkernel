from mpremote.commands import do_filesystem

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "-r",
    "--recursive",
    action="store_true",
    help="recursive copy (for cp command only)",
)
@arg(
    "-v",
    "--verbose",
    action="store_true",
    default=False,
    help="enable verbose output",
)
@arg("path", nargs="*", default=["/"], help="paths (default: /)")
@arg("command", nargs=1, help="filesystem command (e.g. cat, cp, ls, rm, touch)")
@line_magic
def fs_magic(kernel: MpKernel, args):
    """File system commands.

    <command> may be:

    cat <file..> to show the contents of a file or files on the device
        BUG: does not handle unicode characters!

    ls to list the current directory

    ls <dirs...> to list the given directories

    cp [-r] <src...> <dest> to copy files

    rm <src...> to remove files on the device

    mkdir <dirs...> to create directories on the device

    rmdir <dirs...> to remove directories on the device

    touch <file..> to create the files (if they don’t already exist)

    The cp command uses a convention where a leading : represents a remote path.
    Without a leading : means a local path. This is based on the convention used
    by the Secure Copy Protocol (scp) client. All other commands implicitly assume
    the path is a remote path, but the : can be optionally used for clarity.

    Examples:
       # copy main.py from the current local directory to the remote filesystem:
       fs cp main.py :main.py

       # copy main.py from the remote filesystem to the current local directory:
       fs cp :main.py main.py
    """
    do_filesystem(kernel.state, args)


@line_magic
def df_magic(kernel: MpKernel, _):
    """Display remote filesystem disk usage."""
    kernel.exec_remote(_df_func)


_df_func = """
import os
_f = "{:<12s}{:<12s}{:<12s}{:<12s}{:<12s}"
print(_f.format("mount", "size", "used", "avail", "use%"))
_f = _f.replace('s', 'd')
_f = _f.replace('d', 's', 1)
for _m in [''] + os.listdir('/'):
    _s = os.stat('/' + _m)
    if not _s[0] & 1 << 14: 
        continue
    _s = os.statvfs(_m)
    if _s[0]:
        _size = _s[0] * _s[2]; 
        _free = _s[0] * _s[3]; 
    print(_f.format(_m, _size, _size - _free, _free, int(100 * (_size - _free) / _size)))
"""
