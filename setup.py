import os

from setuptools import setup, Extension
from pathlib import Path
import sys
from setuptools.command.build_ext import build_ext
from typing import Tuple, Optional

if sys.version_info[0] == 2:
    sys.exit("Python 2 is not supported.")


import platform
system=platform.system()


# https://github.com/pypa/pip/issues/7953
import site

site.ENABLE_USER_SITE = "--user" in sys.argv[1:]


# Bypass import numpy before running install_requires
# https://stackoverflow.com/questions/54117786/add-numpy-get-include-argument-to-setuptools-without-preinstalled-numpy
class get_numpy_include:
    def __str__(self):
        import numpy

        return numpy.get_include()


def detect_win32_sdk_include_and_library_dirs() -> Optional[Tuple[str, str]]:
    # get program_files path
    for k in ("ProgramFiles", "PROGRAMFILES"):
        if k in os.environ:
            program_files = Path(os.environ[k])
            break
    else:
        program_files = Path("C:\\Program Files\\")
    # search through program_files
    arch = os.getenv("PROCESSOR_ARCHITECTURE", "amd64")
    for dir in sorted(program_files.glob("Azure Kinect SDK v*"), reverse=True):
        include = dir / "sdk" / "include"
        lib = dir / "sdk" / "windows-desktop" / arch / "release" / "lib"
        if include.exists() and lib.exists():
            return str(include), str(lib)
    return None


def detect_and_insert_sdk_include_and_library_dirs(include_dirs, library_dirs) -> None:
    if sys.platform == "win32":
        r = detect_win32_sdk_include_and_library_dirs()
    else:
        # Only implemented for windows
        r = None

    if r is None:
        print("Automatic kinect SDK detection did not yield any results.")
    else:
        include_dir, library_dir = r
        print(f"Automatically detected kinect SDK. Adding include dir: {include_dir} and library dir {library_dir}.")
        include_dirs.insert(0, include_dir)
        library_dirs.insert(0, library_dir)


include_dirs = [get_numpy_include()]
library_dirs = []
if system == 'Windows':
    detect_and_insert_sdk_include_and_library_dirs(include_dirs, library_dirs)
    include_dirs.insert(0,"C:/Program Files/Azure Kinect Body Tracking SDK/sdk/include")
    library_dirs.insert(0,"C:/Program Files/Azure Kinect Body Tracking SDK/sdk/windows-desktop/amd64/release/bin")
    library_dirs.insert(0,"C:/Program Files/Azure Kinect Body Tracking SDK/sdk/windows-desktop/amd64/release/lib")

elif system == 'Linux':
    detect_and_insert_sdk_include_and_library_dirs(include_dirs, library_dirs)
    include_dirs.insert(0,"/usr/local/include")
    include_dirs.insert(0,"/usr/include")
    library_dirs.insert(0,"/usr/local/lib")

k4a_module = Extension(
    "k4a_module",
    sources=["pyk4a/pyk4a.cpp"],
    libraries=["k4a", "k4arecord"],
    include_dirs=include_dirs,
    library_dirs=library_dirs,
)

class pyk4a_build_ext(build_ext):
    user_options = build_ext.user_options + [('enable-body-tracking', None, 'Compile with body-tracking support'), ]
    boolean_options = build_ext.boolean_options + ['enable-body-tracking', ]

    def initialize_options(self):
        self.enable_body_tracking = True
        build_ext.initialize_options(self)

    def finalize_options(self):
        build_ext.finalize_options(self)

    def build_extensions(self):
        # modify k4a_module extension depending on arguments like "--enable-body-tracking"
        assert k4a_module in self.extensions
        if self.enable_body_tracking:
            k4a_module.libraries.append('k4abt')
            k4a_module.define_macros.append(('ENABLE_BODY_TRACKING', '1'))

        build_ext.build_extensions(self)

setup(
    ext_modules=[k4a_module],
    cmdclass={'build_ext': pyk4a_build_ext},
)
