import sys

from ipykernel.kernelbase import Kernel
from mpremote.main import State
from mpremote.transport import TransportError

from .magic import CELL_MAGIC, LINE_MAGIC


class EchoKernel(Kernel):
    implementation = "Echo"
    implementation_version = "1.0"
    language = "no-op"
    language_version = "0.1"
    language_info = {
        "name": "echo",
        "mimetype": "text/plain",
        "file_extension": ".txt",
    }
    banner = "Echo kernel - as useful as a parrot"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = State()
        self.state._auto_soft_reset = False

    def do_execute(  # type: ignore
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):
        self.redirect_stdout_stderr()
        # split code into cells
        code = "remote\n" + code  # remote is the default environment
        cells = code.strip().split("\n%%")
        for cell in cells:
            head, _, code = cell.partition("\n")
            magic, args = (head + " ").split(" ", 1)
            method = CELL_MAGIC.get(magic)
            if not method:
                print(f"Unknown cell magic: %%{magic}", file=sys.stderr)
            else:
                try:
                    res = method[0](self, args, code)
                    if res:
                        return res
                except Exception as e:
                    print(f"Error executing cell magic {args}: {e}", file=sys.stderr)

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def exec_remote(self, code, *, silent=False, data_consumer=None):
        """Execute the given code on the remote device."""
        code = code.strip()
        if len(code) == 0:
            return
        set_time = self.state.transport is None
        self.state.ensure_raw_repl(soft_reset=False)
        if set_time:
            # always sync clock (e.g. for file modification times)
            rtc.sync_time(self, None)
        self.state.did_action()
        try:
            self.state.transport.exec_raw_no_follow(code)  # type: ignore
            _, err = self.state.transport.follow(  # type: ignore
                timeout=None,
                data_consumer=None if silent else data_consumer or self.data_consumer,
            )
            if len(err) > 0:
                print(err.decode().strip(), file=sys.stderr)
        except TransportError as e:
            print(str(e), file=sys.stderr)

    def data_consumer(self, data):
        if not data:
            return
        if isinstance(data, bytes):
            try:
                data = data.decode()
            except UnicodeDecodeError:
                pass
        data = data.replace("\x04", "")  # type: ignore
        if data:
            print(data, end="")

    def redirect_stdout_stderr(self):
        # print crashes kernel, so we just redirect

        class PrintIO:
            def __init__(self, kernel, stream="stdout"):
                self.kernel = kernel
                self.stream = stream
                self.buffer = self  # for mpremote

            def write(self, data):
                if isinstance(data, bytes):
                    data = data.decode()
                stream_content = {
                    "name": self.stream,
                    "text": data,
                }
                self.kernel.send_response(
                    self.kernel.iopub_socket, "stream", stream_content
                )

            def flush(self):
                pass

            def isatty(self):
                return False

        sys.stdout = PrintIO(self)
        sys.stderr = PrintIO(self, "stderr")


# import everything to include in CELL_MAGIC and LINE_MAGIC
# we do this here rather than in .magic to avoid circular imports

# ruff: noqa: E402, F401
from .magic import (
    cd,
    connect,
    fs,
    lsmagic,
    mip,
    mount,
    remote,
    reset,
    rsync,
    rtc,
    run,
    shell,
    uid,
    writefile,
)
