from ..kernel import MpKernel
from . import CELL_MAGIC, LINE_MAGIC, arg, line_magic


@arg(
    "-v",
    "--verbose",
    action="store_true",
    help="Show detailed help for each line magic.",
)
@line_magic
def lsmagic_magic(kernel: MpKernel, args):
    """List all magic functions"""
    if args.verbose:
        for k, v in sorted(LINE_MAGIC.items()):
            if not v[1]:
                continue
            print(f"MAGIC %{k} {'-'*(70-len(k))}")
            v[0](kernel, "-h")
            print("\n")
        return

    print("Line Magic:    -h shows help (e.g. %connect -h)")
    for k, v in sorted(LINE_MAGIC.items()):
        if not v[1]:
            continue
        print("  %{:10s}  {}".format(k, v[1]))
    print("  {:11s}  {}".format("!", "Pass line to shell for evaluation"))
    print("\nCell Magic:    -h shows help (e.g. %%writefile -h)")
    for k, v in sorted(CELL_MAGIC.items()):
        if not v[1]:
            continue
        print("  %%{:10s} {}".format(k, v[1]))
