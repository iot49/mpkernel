from ..kernel import MpKernel
from . import line_magic


@line_magic
def uid_magic(kernel: MpKernel, _, __):
    """Print the uid (machine.unique_id()) of the remote device."""
    kernel.exec_remote(_uid_func)


_uid_func = """
uid = bytes(6)
try:
    import machine
    uid = machine.unique_id()
except:
    import microcontroller
    uid = microcontroller.cpu.uid
import sys
print(":".join("{:02x}".format(x) for x in uid), end="")
"""
