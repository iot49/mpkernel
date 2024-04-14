from mpremote.commands import do_mount, do_umount

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "-l",
    "--unsafe-links",
    action="store_true",
    help="""Follow symbolic links pointing outside of local directory.
    By default an error will be raised if the device accesses a file or 
    directory which is outside (up one or more directory levels) the 
    local directory that is mounted. This option disables this check 
    for symbolic links, allowing the device to follow symbolic links 
    outside of the local directory.""",
)
@arg(
    "path",
    nargs="?",
    default=["./remote"],
    help="local directory to mount on remote device",
)
@line_magic
def mount_magic(kernel: MpKernel, args):
    """Mount local directory on remote device.

    This allows the remote device to see the local host directory as if it were its
    own filesystem. This is useful for development, and avoids the need to copy files
    to the device while you are working on them.

    The device installs a filesystem driver, which is then mounted in the device VFS
    as /remote, which uses the serial connection to mpremote as a side-channel to
    access files. The device will have its current working directory (via os.chdir)
    set to /remote so that imports and file access will occur there instead of the
    default filesystem path while the mount is active.

    During usage, a soft-reset will dismount, then automatically remount the directory.
    If the unit has a main.py running at startup however the remount cannot occur. In
    this case a raw mode soft reboot can be used: Ctrl-A Ctrl-D to reboot, then Ctrl-B
    to get back to normal repl at which point the mount will be ready.
    """
    do_mount(kernel.state, args)


@arg(
    "path",
    nargs="?",
    default=["./remote"],
    help="local directory to mount on remote device",
)
@line_magic
def umount_magic(kernel: MpKernel, args):
    """Unmount local directory from remote device."""
    do_umount(kernel.state, args.path[0])
