import re
import sys
import time
from subprocess import PIPE, STDOUT, Popen

from serial.serialutil import SerialException

from ..kernel import MpKernel
from . import LINE_MAGIC, cell_magic


def line_magic(kernel: MpKernel, line):
    if line.startswith("!"):
        with Popen(
            line[1:],
            shell=True,
            stdout=PIPE,
            stderr=STDOUT,
            close_fds=True,
            executable="/bin/bash",
        ) as process:
            for line in iter(process.stdout.readline, b""):  # type: ignore
                print(line.rstrip().decode("utf-8"))
        return
    m = re.match(r"%([^ ]*)( .*)?", line)
    if not m:
        print(f"1 Syntax error: '{line.encode()}'\n", file=sys.stderr)
        return
    name = m.group(1)
    rest = m.group(2)
    rest = (rest or "").strip()
    method = LINE_MAGIC.get(name)
    if method:
        method[0](kernel, rest)
    else:
        print(f"Line magic %{name} not defined", file=sys.stderr)


@cell_magic
def remote_magic(kernel: MpKernel, args, code):
    """Evaluate code on remote device

    Example:
      %%remote
      import os
      print(os.listdir())
    """
    for s in re.split(r"(?<=\n)([%!][^\n]*)", code):
        s = s.strip()
        if not s:
            continue
        try:
            if s.startswith("%") or s.startswith("!"):
                try:
                    magic, s = s.split("\n", 1)
                    line_magic(kernel, magic)
                except ValueError:
                    line_magic(kernel, s)
                    s = ""
            kernel.exec_remote(s)
            print()
        except SystemExit:
            # mpremote is in the habit of calling sys.exit
            pass
        except SerialException:
            # print("Serial port closed", file=sys.stderr)
            kernel.state.transport = None
            # give the device time to reboot
            time.sleep(1)
