from subprocess import PIPE, STDOUT, Popen

from ..kernel import EchoKernel
from . import arg, cell_magic


@arg("-s", "--shell", help="Shell to use", default="/bin/bash")
@cell_magic
def shell_magic(kernel: EchoKernel, args, code):
    """Pass cell to shell for evaluation

    Example:
      %%shell
      printenv
    """
    with Popen(
        code,
        stdout=PIPE,
        stderr=STDOUT,
        shell=True,
        close_fds=True,
        executable=args.shell,
    ) as process:
        for line in iter(process.stdout.readline, b""):  # type: ignore
            print(line.rstrip().decode("utf-8"))
