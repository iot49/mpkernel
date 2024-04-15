import datetime
import time
from io import BytesIO

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "-s",
    "--set",
    action="store_true",
    help="Synchronize remote time to UTC.",
)
@line_magic
def rtc_magic(kernel: MpKernel, args):
    """Display remote time in host's TZ. Optionally set the remote clock to host's time."""
    if args.set:
        sync_time(kernel)
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


def sync_time(kernel: MpKernel):
    """Sync the device clock (RTC) to the host PC’s time (TZ=UTC)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    timetuple = "({}, {}, {}, {}, {}, {}, {}, {})".format(
        now.year,
        now.month,
        now.day,
        now.weekday(),
        now.hour,
        now.minute,
        now.second,
        now.microsecond,
    )
    kernel.exec_remote("import machine; machine.RTC().datetime({})".format(timetuple))
