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
@arg("path", nargs="*", help="Path to the directories to list.")
@line_magic
def rlist_magic(kernel: MpKernel, args):
    """List files

    Examples:

        %rlist                # List all (path = $MP_REMOTE_PATH or "/")
                              # files on remote machine
        %rlist -l ./local     # List directory ./local on local machine
    """
    path = args.path if args.path else ["."] if args.local else ["/"]
    # get list of files
    files = []
    for p in path:
        files.extend(local_list(p) if args.local else remote_list(kernel, p))
    if len(files) == 0:
        print(f"{Fore.green}no files")
    for file in files:
        dir, level, path, mtime, sz = file.split(",")
        level = int(level)
        path = os.path.basename(eval(path))
        mtime = (
            datetime.datetime.fromtimestamp(int(mtime), datetime.UTC)
            .astimezone()
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        if dir == "D":
            print(f"{' ':7}  {' ':19} {'    '*level} {Fore.green}{path}/")
        else:
            print(f"{int(sz):7}  {mtime:18} {'    '*level} {Fore.cyan}{path}")
        print(Style.reset, end="")


@arg(
    "--dry-run",
    action="store_true",
    help="Only show differences, do actually sync files.",
)
@arg(
    "--no-delete",
    action="store_true",
    help="Do not delete files on the remote.",
)
@arg(
    "--include",
    nargs="*",
    default=["*.py", "*.mpy"],
    help="List of file patterns to include. Default: ['*.py', '*.mpy']. Note: put after local_path to avoid amgiguity.",
)
@arg(
    "--exclude",
    nargs="*",
    default=["*__pycache__*"],
    help="List of file patterns to exclude. Default: ['*__pycache__*']. Note: put after local_path to avoid amgiguity.",
)
@arg(
    "--remote_path",
    nargs="?",
    default=os.getenv("MP_REMOTE_PATH", "/"),
    help="Path to directory on remote. Defaults to $MP_REMOTE_PATH or root (/) if not specified.",
)
@arg(
    "local_path",
    nargs="*",
    help="Directories on host. Defaults to $MP_LOCAL_PATH. Separate multiple paths with colon (:).",
)
@line_magic
def rsync_magic(kernel: MpKernel, args):
    """Synchronize local to remote by sending differences from local to remote.

    Note 1: Only sends files from local to remote. Use %fs cp magic to copy files
            from remote to local.

    Note 2: Files created on the remote will be deleted unless specifically excluded by
            either --exclude or setting --upload-only.

    Examples:

        %rsync  # Sync local (host) to remote (MicroPython)
    """
    local_files = FileList(
        local=True,
        path=args.local_path,
        include=args.include,
        exclude=args.exclude,
        kernel=kernel,
    ).files
    remote_files = FileList(
        local=False,
        path=args.remote_path,
        include=args.include,
        exclude=args.exclude,
        kernel=kernel,
    ).files

    # print(json.dumps(local_files, indent=2))
    # print(json.dumps(remote_files, indent=2))

    # compute differences
    lk = local_files.keys()
    rk = remote_files.keys()
    to_del = sorted(rk - lk)
    to_add = sorted(lk - rk)
    to_upd = set()
    for u in rk & lk:
        # update?
        rf = remote_files[u]
        lf = local_files[u]
        if local_files[u]["is_dir"]:
            continue
        if (
            rf["is_dir"] != lf["is_dir"]
            or rf["level"] != lf["level"]
            or rf["size"] != lf["size"]
            or rf["mtime"] < lf["mtime"] - 10
        ):
            to_upd.add(u)
    to_upd = sorted(to_upd)

    if len(to_del) + len(to_add) + len(to_upd) == 0:
        print(f"{Fore.green}Local and remote directories match{Style.reset}")
        return

    if len(to_del) > 0:
        print(f"{Fore.red}Delete")
        for f in to_del:
            print(f"  {f}")
            if not args.dry_run and not args.no_delete:
                rm_rf(kernel, f)

    if len(to_add) > 0:
        print(f"{Fore.green}Add")
        for f in to_add:
            print(f"  {f}")
            if not args.dry_run and not local_files[f]["is_dir"]:
                src = os.path.join(local_files[f]["abs_path"], f)
                dst = os.path.join(args.remote_path, f)
                fput(kernel, src, dst)

    if len(to_upd) > 0:
        print(f"{Fore.cyan}Update")
        for f in to_upd:
            print(f"  {f}")
            if not args.dry_run:
                src = os.path.join(local_files[f]["abs_path"], f)
                dst = os.path.join(args.remote_path[0], f)
                fput(kernel, src, dst)

    print(Style.reset, end="")


class FileList:
    def __init__(
        self,
        *,
        local: bool,
        path: list[str],
        include: list[str],
        exclude: list[str],
        kernel: MpKernel,
    ):
        # default directory paths
        if len(path) == 0:
            if local:
                path = os.getenv("MP_LOCAL_PATH", "./local").split(":")
            else:
                path = os.getenv("MP_REMOTE_PATH", "/").split(":")
        # get list of files
        self.files = {}
        for p in path:
            file_list = local_list(p) if local else remote_list(kernel, p)
            filtered_list = self.filter(file_list, include, exclude)
            self.files |= self.as_map(filtered_list, p)

    def filter(self, files, include, exclude):
        inc = [False] * len(files)
        for n, f in enumerate(files):
            if f.startswith("D"):
                # always include directories or the display looks weird
                inc[n] = True
            path = eval(f.split(",")[2])
            if path.startswith("/"):
                path = path[1:]
            for i in include:
                if fnmatch(path, i):
                    inc[n] = True
            for e in exclude:
                if fnmatch(path, e):
                    inc[n] = False
        return [f for n, f in enumerate(files) if inc[n]]

    def as_map(self, files, abs_path):
        map = {}
        for f in files:
            kind, level, path, mtime, size = f.split(",")
            path = eval(path)
            if path.startswith("/"):
                path = path[1:]
            map[path] = {
                "is_dir": kind == "D",
                "level": int(level),
                "mtime": float(mtime),
                "size": int(size),
                "abs_path": abs_path,
            }
        return map


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
