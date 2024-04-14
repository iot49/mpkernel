import time
from io import BytesIO

from mpremote.commands import do_rtc

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "-s",
    "--set",
    action="store_true",
    help="Set the device RTC to the host PC’s current time.",
)
@line_magic
def rtc_magic(kernel: MpKernel, args):
    """Set/get the device clock (RTC)."""
    if args.set:
        do_rtc(kernel.state, args)
    else:
        # fetch time from device and format on the host
        # Note: use localtime since many micropython ports don't use UNIX epoch
        buf = BytesIO()
        kernel.exec_remote(
            "import time; print(tuple(time.localtime()), end='')",
            data_consumer=buf.write,
        )
        t = buf.getvalue().decode()
        t = eval(t.replace("\x04", ""))
        if len(t) < 9:
            t += (-1,)
        t = time.strftime("%Y-%b-%d %H:%M:%S", time.localtime(time.mktime(t)))
        print(t)


def sync_time(kernel: MpKernel, _):
    """Sync the device clock (RTC) to the host PC’s time."""

    class Namespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    do_rtc(kernel.state, Namespace(set=True))
