#!/usr/bin/env python3
"""
Writes out the source and include files needed for AutoTools.

This script will update the collected_files.md file.
"""
import os

from typing import Iterable, Sequence, Tuple

import re

BANNER = "# This file was automatically generated by scripts/update_sources.py"


VENDOR_SOURCES = (
    "src/vendor/glad.c",
    "src/vendor/lodepng.c",
    "src/vendor/stb.c",
    "src/vendor/utf8proc/utf8proc.c",
)


def get_sources(
    sources: bool = False, includes: bool = False
) -> Iterable[Tuple[str, Sequence[str]]]:
    """Iterate over sources and headers with sub-folders grouped together."""
    re_inclusion = []
    if sources:
        re_inclusion.append("c|cpp")
    if includes:
        re_inclusion.append("h|hpp")
    re_valid = re.compile(r".*\.(%s)$" % ("|".join(re_inclusion),))

    for curpath, dirs, files in os.walk("src/libtcod"):
        # Ignore hidden directories.
        dirs[:] = [dir for dir in dirs if not dir.startswith(".")]
        files = [
            os.path.join(curpath, f).replace("\\", "/")
            for f in files
            if re_valid.match(f)
        ]
        group = os.path.relpath(curpath, "src").replace("\\", "/")
        yield group, files
    if sources:
        yield "vendor", VENDOR_SOURCES


def all_sources(includes: bool = False) -> Iterable[str]:
    """Iterate over all sources needed to compile libtcod."""
    for _, sources in get_sources(sources=True, includes=includes):
        yield from sources


def generate_am() -> str:
    """Returns an AutoMake script.

    This might be run on Windows, so it must return Unix file separators.
    """
    out = f"{BANNER}\n"
    for group, files in get_sources(sources=False, includes=True):
        include_name = group.replace("/", "_")
        files = ["../../" + f for f in files]
        out += f"\n{include_name}_includedir = $(includedir)/{group}"
        out += f"\n{include_name}_include_HEADERS = \\"
        out += "\n\t" + " \\\n\t".join(files)
        out += "\n"

    out += "\nlibtcod_la_SOURCES = \\"
    out += "\n\t" + " \\\n\t".join("../../" + f for f in all_sources())
    out += "\n"
    return out


def generate_cmake() -> str:
    """Returns a CMake script with libtcod's sources."""
    out = f"{BANNER}"
    out += "\ntarget_sources(TCOD PRIVATE\n    "
    out += "\n    ".join(os.path.relpath(f, "src") for f in all_sources(includes=True))
    out += "\n)"
    for group, files in get_sources(sources=True, includes=True):
        group = group.replace("/", r"\\")
        out += f"\nsource_group({group} FILES\n    "
        out += "\n    ".join(os.path.relpath(f, "src") for f in files)
        out += "\n)"
    out += "\n"
    return out


def main() -> None:
    # Change to project root directory, using this file as a reference.
    os.chdir(os.path.join(os.path.split(__file__)[0], ".."))

    with open("buildsys/autotools/sources.am", "w") as file:
        file.write(generate_am())
    with open("src/sources.cmake", "w") as file:
        file.write(generate_cmake())


if __name__ == "__main__":
    main()
