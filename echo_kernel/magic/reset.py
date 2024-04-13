from mpremote.commands import do_soft_reset

from ..kernel import EchoKernel
from . import line_magic


@line_magic
def softreset_magic(kernel: EchoKernel, _):
    """Clear out the Python heap and restart the interpreter."""
    do_soft_reset(kernel.state)


@line_magic
def reset_magic(kernel: EchoKernel, _):
    """Hard reset the remote device by calling machine.reset()."""
    kernel.exec_remote("import time, machine; time.sleep_ms(100); machine.reset()")


@line_magic
def bootloader_magic(kernel: EchoKernel, _):
    """Make the device enter its bootloader by calling machine.bootloader()."""
    kernel.exec_remote("import time, machine; time.sleep_ms(100); machine.bootloader()")
