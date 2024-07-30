import os
from io import BytesIO

from .kernel import MpKernel


def rm_rf(kernel: MpKernel, path: str, r: bool = True, f: bool = True):
    """rm -rf path"""
    kernel.exec_remote(f"{_rm_rf_func}\nrm_rf({repr(path)}, {r}, {f})")


def makedirs(kernel: MpKernel, path: str):
    """makedirs path"""
    kernel.exec_remote(f"{_makedirs_func}\nmakedirs({repr(path)})")


def fput(kernel: MpKernel, local_path: str, remote_path: str, chunk_size=256):
    makedirs(kernel, os.path.dirname(remote_path))
    kernel.exec_remote(f"_f=open('{remote_path}','wb');_w=_f.write")
    with open(local_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            kernel.exec_remote(f"_w({repr(data)})")
    kernel.exec_remote("_f.close()")


def remote_list(kernel: MpKernel, path):
    buf = BytesIO()
    kernel.exec_remote(
        _list_files.replace("__PATH__", repr(path)), data_consumer=buf.write
    )
    buf = buf.getvalue().decode().replace("\x04", "").strip()
    return buf.split("\r\n") if len(buf) else []


# micropython/lib/shared/timeutils/timeutils.h
# The number of seconds between 1970/1/1 and 2000/1/1 is calculated using:
# time.mktime((2000,1,1,0,0,0,0,0,0)) - time.mktime((1970,1,1,0,0,0,0,0,0))
# define TIMEUTILS_SECONDS_1970_TO_2000 (946684800ULL)

_list_files = """
import os, time
EPOCH_OFFSET = 946684800 if time.gmtime(0)[0] == 2000 else 0

def _list(path, level=-1, full_path=""):
    stat = os.stat(path)
    fsize = stat[6]
    mtime = stat[7] + EPOCH_OFFSET
    if stat[0] & 0x4000:
        up = os.getcwd()
        os.chdir(path)
        if level >= 0:
            print(f"D,{level},{repr(full_path)},{mtime},0")
        for p in sorted(os.listdir()):
            _list(p, level + 1, full_path + "/" + p)
        os.chdir(up)
    else:
        print(f"F,{level},{repr(full_path)},{mtime},{fsize}")

_list(__PATH__)
"""

_makedirs_func = """
import os
def makedirs(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.args[0]==2:
            makedirs(path[:path.rfind('/')])
            os.mkdir(path)
        elif e.args[0]==17:
            pass
        else:
            raise
"""

_rm_rf_func = """
import os
def rm_rf(path, r, f):
    try:
        mode = os.stat(path)[0]
    except OSError:
        return
    if mode & 0x4000 != 0:
        if r:
            for file in os.listdir(path):
                rm_rf(path + '/' + file, r, f)
        if f:
            try:
                os.rmdir(path)
            except OSError:
                pass
    else:
        os.remove(path)
"""
