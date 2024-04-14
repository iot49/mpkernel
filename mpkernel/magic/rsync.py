import datetime
import os
from fnmatch import fnmatch

from colored import Fore, Style

from ..kernel import MpKernel
from ..remote_ops import fput, remote_list, rm_rf
from . import arg, line_magic


@arg(
    "-l",
    "--local",
    action="store_true",
    help="List files on local, rather than remote machine.",
)
@arg(
    "--include",
    nargs="*",
    default=["*"],
    help="List of file patterns to include. Default: include all files (*). Note: put after path to avoid amgiguity.",
)
@arg(
    "--exclude",
    nargs="*",
    default=[],
    help="List of file patterns to exclude. Default: exclude no files. Note: put after path to avoid amgiguity.",
)
@arg(
    "path",
    nargs="?",
    default=None,
    help="Path to the file or directory to list. Defaults to $MP_REMOTE_PATH or $MP_LOCAL_PATH with -l option.",
)
@line_magic
def rlist_magic(kernel: MpKernel, args):
    """List files

    Examples:

        %rlist                # List all (path = $MP_REMOTE_PATH or "/")
                              # files on remote machine
        %rlist -l ./local     # List directory ./local on local machine

        # list only files with .py or .mpy extension, but exclude boot.py
        # this is particularly useful for related commands, %rsync and %rdiff

        %rlist / --include *.py *.mpy --exclude boot.py
    """
    if args.path is None:
        env = "MP_LOCAL_PATH" if args.local else "MP_REMOTE_PATH"
        default = "./local" if args.local else "/"
        args.path = os.getenv(env, default)
    files = local_list(args.path) if args.local else remote_list(kernel, args.path)
    show(filter(files, include=args.include, exclude=args.exclude))


@arg(
    "-n",
    "--dry-run",
    action="store_true",
    help="Only show differences, do actually sync files.",
)
@arg(
    "-x",
    "--upload-only",
    action="store_true",
    help="Only upload changes, do not delete any files on remote.",
)
@arg(
    "--include",
    nargs="*",
    default=["*"],
    help="List of file patterns to include. Default: include all files (*). Note: put after path to avoid amgiguity.",
)
@arg(
    "--exclude",
    nargs="*",
    default=[],
    help="List of file patterns to exclude. Default: exclude no files. Note: put after path to avoid amgiguity.",
)
@arg(
    "local_path",
    nargs="?",
    default=os.getenv("MP_LOCAL_PATH", "./local"),
    help="Path to directory on host. Defaults to $MP_LOCAL_PATH or ./local.",
)
@arg(
    "remote_path",
    nargs="?",
    default=os.getenv("MP_REMOTE_PATH", "/"),
    help="Path to directory on remote. Defaults to $MP_REMOTE_PATH or /.",
)
@line_magic
def rsync_magic(kernel: MpKernel, args):
    """Synchronize local to remote by sending differences from local to remote.

    Note 1: Only sends files from local to remote. Use cp to copy files
            from remote to local.

    Note 2: Files created on the remote will be deleted. Excluding these
            files (--exclude) or setting --upload-only will prevent this.

    Examples:

        %rsync                # Sync remote to local
    """
    local_files = local_list(args.local_path)
    local_files = filter(local_files, include=args.include, exclude=args.exclude)
    local_files = as_map(local_files)
    remote_files = remote_list(kernel, args.remote_path)
    remote_files = filter(remote_files, include=args.include, exclude=args.exclude)
    remote_files = as_map(remote_files)
    to_del, to_add, to_upd = diff(local_files, remote_files)

    if len(to_del) + len(to_add) + len(to_upd) == 0:
        print(f"{Fore.green}Local and remote directories match{Style.reset}")
        return

    if len(to_del) > 0:
        print(f"{Fore.red}Delete")
        for f in to_del:
            print(f"  {f}")
            if not args.dry_run and not args.upload_only:
                rm_rf(kernel, f)

    if len(to_add) > 0:
        print(f"{Fore.green}Add")
        for f in to_add:
            print(f"  {f}")
            if not args.dry_run:
                fput(kernel, os.path.join(args.local_path, f), f)

    if len(to_upd) > 0:
        print(f"{Fore.cyan}Update")
        for f in to_upd:
            print(f"  {f}")
            if not args.dry_run:
                # remove - if destination exists and is a directory, an attempt to overwrite fails
                print(f"  REMOVING {f}")
                rm_rf(kernel, f, False, False)
                # fput(kernel, os.path.join(args.local_path, f), f)

    print(Style.reset, end="")


def sync(kernel, diff):
    to_del, to_add, to_upd = diff
    for f in to_del:
        kernel.exec_remote(f"import os; os.remove({repr(f)})")


def local_list(path, files=None, level=-1, full_path=""):
    if files is None:
        files = []
    stat = os.stat(path)
    fsize = stat[6]
    mtime = stat[7]
    if stat[0] & 0x4000:
        up = os.getcwd()
        os.chdir(path)
        if level >= 0:
            files.append(f"D,{level},{repr(full_path)},{mtime},0")
        for p in sorted(os.listdir()):
            local_list(p, files, level + 1, full_path + "/" + p)
        os.chdir(up)
    else:
        files.append(f"F,{level},{repr(full_path)},{mtime},{fsize}")
    return files


def filter(files, include, exclude):
    inc = [False] * len(files)
    for n, f in enumerate(files):
        if f.startswith("D"):
            # always include directories or the display looks weird
            inc[n] = True
            continue
        path = eval(f.split(",")[2])
        for i in include:
            if fnmatch(path, i):
                inc[n] = True
        for e in exclude:
            if fnmatch(path, e):
                inc[n] = False
    return [f for n, f in enumerate(files) if inc[n]]


def show(files):
    for f in files:
        kind, level, path, mtime, size = f.split(",")
        level = int(level)
        path = os.path.basename(eval(path))
        mtime = datetime.datetime.fromtimestamp(float(mtime), datetime.UTC).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if kind == "D":
            print(f"{' ':7}  {' ':18}  {'    '*level} {Fore.green}{path}/")
        else:
            print(f"{int(size):7}  {mtime:18} {'    '*level} {Fore.cyan}{path}")
        print(Style.reset, end="")


def as_map(files):
    map = {}
    for f in files:
        kind, level, path, mtime, size = f.split(",")
        if kind == "D":
            continue
        path = eval(path)
        if path.startswith("/"):
            path = path[1:]
        map[path] = (kind, int(level), float(mtime), int(size))
    return map


def diff(local, remote):
    lk = local.keys()
    rk = remote.keys()
    to_del = rk - lk
    to_add = lk - rk
    to_upd = set()
    for u in rk & lk:
        rd, rl, rmt, rsz = remote[u]
        ld, ll, lmt, lsz = local[u]
        # modification time is always off by a lot ???
        if rd != ld or rsz != lsz:  #  or rmt < lmt:
            # print(f"Update based on modif time: {rmt < lmt} delta = {rmt - lmt}")
            to_upd.add(u)
    return sorted(to_del), sorted(to_add), sorted(to_upd)
