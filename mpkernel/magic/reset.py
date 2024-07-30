import sys

from mpremote.commands import do_soft_reset

from ..kernel import MpKernel
from . import line_magic


@line_magic
def softreset_magic(kernel: MpKernel, _):
    """Clear out the Python heap and restart the interpreter."""
    do_soft_reset(kernel.state)
    print("----- soft reset", file=sys.stderr)


@line_magic
def reset_magic(kernel: MpKernel, _):
    """Hard reset the remote device by calling machine.reset()."""
    kernel.exec_remote("import time, machine; time.sleep_ms(100); machine.reset()")
    print("----- machine.reset()", file=sys.stderr)


@line_magic
def bootloader_magic(kernel: MpKernel, _):
    """Make the device enter its bootloader by calling machine.bootloader()."""
    kernel.exec_remote("import time, machine; time.sleep_ms(100); machine.bootloader()")
    print("----- machine.bootloader()", file=sys.stderr)
