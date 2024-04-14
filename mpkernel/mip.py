# MicroPython package installer
# MIT license; Copyright (c) 2022 Jim Mussared

# modified version of
# https://github.com/micropython/micropython-lib/blob/master/micropython/mip/mip/__init__.py

import os
import sys

import requests

_PACKAGE_INDEX = "https://micropython.org/pi/v2"
_CHUNK_SIZE = 128


# This implements os.makedirs(os.dirname(path))
def _ensure_path_exists(path):
    import os

    split = path.split("/")

    # Handle paths starting with "/".
    if not split[0]:
        split.pop(0)
        split[0] = "/" + split[0]

    prefix = ""
    for i in range(len(split) - 1):
        prefix += split[i]
        try:
            os.stat(prefix)
        except:
            os.mkdir(prefix)
        prefix += "/"


def _chunk(src, dest):
    buf = memoryview(bytearray(_CHUNK_SIZE))
    while True:
        n = src.readinto(buf)
        if n == 0:
            break
        dest(buf if n == _CHUNK_SIZE else buf[:n])


# Check if the specified path exists and matches the hash.
def _check_exists(path, short_hash):
    try:
        import binascii
        import hashlib

        with open(path, "rb") as f:
            hs256 = hashlib.sha256()
            _chunk(f, hs256.update)
            existing_hash = str(
                binascii.hexlify(hs256.digest())[: len(short_hash)], "utf-8"
            )
            return existing_hash == short_hash
    except:
        return False


def _rewrite_url(url, branch=None):
    if not branch:
        branch = "HEAD"
    if url.startswith("github:"):
        url = url[7:].split("/")
        url = (
            "https://raw.githubusercontent.com/"
            + url[0]
            + "/"
            + url[1]
            + "/"
            + branch
            + "/"
            + "/".join(url[2:])
        )
    return url


def _download_file(url, dest):
    response = requests.get(url)
    try:
        if response.status_code != 200:
            print("Error", response.status_code, "requesting", url)
            return False

        print("Copying to", dest)
        _ensure_path_exists(dest)
        with open(dest, "wb") as f:
            # _chunk(response.raw, f.write)
            for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                f.write(chunk)

        return True
    finally:
        response.close()


def _install_json(package_json_url, index, target, version, mpy, overwrite):
    response = requests.get(_rewrite_url(package_json_url, version))
    try:
        if response.status_code != 200:
            print("Package not found:", package_json_url)
            return False

        package_json = response.json()
    finally:
        response.close()
    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target + "/" + target_path
        if _check_exists(fs_target_path, short_hash) and not overwrite:
            print(
                f"***** File {target_path} already exists in {os.path.dirname(fs_target_path)} - not overwriting."
            )
        else:
            file_url = "{}/file/{}/{}".format(index, short_hash[:2], short_hash)
            if not _download_file(file_url, fs_target_path):
                print("File not found: {} {}".format(target_path, short_hash))
                return False
    for target_path, url in package_json.get("urls", ()):
        fs_target_path = target + "/" + target_path
        if not _download_file(_rewrite_url(url, version), fs_target_path):
            print("File not found: {} {}".format(target_path, url))
            return False
    for dep, dep_version in package_json.get("deps", ()):
        if not _install_package(dep, index, target, dep_version, mpy, overwrite):
            return False
    return True


def _install_package(package, index, target, version, mpy, overwrite):
    if (
        package.startswith("http://")
        or package.startswith("https://")
        or package.startswith("github:")
    ):
        if package.endswith(".py") or package.endswith(".mpy"):
            print("Downloading {} to {}".format(package, target))
            return _download_file(
                _rewrite_url(package, version), target + "/" + package.rsplit("/")[-1]
            )
        else:
            if not package.endswith(".json"):
                if not package.endswith("/"):
                    package += "/"
                package += "package.json"
            print("Installing {} to {}".format(package, target))
    else:
        if not version:
            version = "latest"
        print(
            "Installing {} ({}) from {} to {}".format(package, version, index, target)
        )

        mpy_version = (
            sys.implementation._mpy & 0xFF
            if mpy and hasattr(sys.implementation, "_mpy")
            else "py"
        )

        package = "{}/package/{}/{}/{}.json".format(
            index, mpy_version, package, version
        )

    return _install_json(package, index, target, version, mpy, overwrite)


def install(package, index=None, target=None, version=None, mpy=True, overwrite=False):
    if not target:
        for p in sys.path:
            if p.endswith("/lib"):
                target = p
                break
        else:
            print("Unable to find lib dir in sys.path")
            return

    if not index:
        index = _PACKAGE_INDEX

    if _install_package(package, index.rstrip("/"), target, version, mpy, overwrite):
        print()
    else:
        print("Package may be partially installed")
