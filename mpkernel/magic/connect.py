import serial.tools.list_ports
from mpremote.commands import do_connect, do_disconnect

from ..kernel import MpKernel
from . import arg, line_magic


@arg(
    "device",
    nargs=1,
    help="Either list, auto, id:x, port:x, or any valid device name/path",
)
@line_magic
def connect_magic(kernel: MpKernel, args):
    """Connect to remote device

    device may be one of:
        list: list available devices
        auto: connect to first available USB serial port (default)
        id:<serial>: connect to the device with USB serial number <serial>
            (the second column from the connect list command output)
        port:<path>: connect to the device with the given path
            (the first column from the connect list command output)
        rfc2217://<host>:<port>: connect to the device using serial over TCP
            (e.g. a networked serial port based on RFC2217)
        any valid device name/path, to connect to that device

    Note: The auto option will only detect USB serial ports, i.e. a serial
        port that has an associated USB VID/PID (i.e. CDC/ACM or FTDI-style devices).
        Other types of serial ports will not be auto-detected.
    Example:
      %connect list
    """
    # handle here with alternative formatting
    if args.device[0] == "list":
        for p in sorted(serial.tools.list_ports.comports()):
            if not isinstance(p.vid, int) or not isinstance(p.pid, int):
                continue
            print(
                "{:30s} {:10s} {:04x}:{:04x} {} {}".format(
                    str(p.device),
                    str(p.serial_number),
                    p.vid,
                    p.pid,
                    p.manufacturer,
                    p.product,
                )
            )
    else:
        do_connect(kernel.state, args)


@line_magic
def disconnect_magic(kernel: MpKernel, args):
    """Disconnect from remote device"""
    do_disconnect(kernel.state)
