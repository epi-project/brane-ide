#!/usr/bin/env python3
# MAKE.py
#   by Lut99
#
# Created:
#   02 Aug 2023, 08:38:41
# Last edited:
#   02 Aug 2023, 09:02:26
# Auto updated?
#   Yes
#
# Description:
#   Make script for the Brane IDE project.
#

import argparse
import os
import platform
import sys
from typing_extensions import Self


##### HELPER FUNCTIONS #####
def supports_color():
    """
        Returns True if the running system's terminal supports color, and False
        otherwise.

        From: https://stackoverflow.com/a/22254892
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

def pwarn(message: str):
    """
        Prints a warning message to stderr with appropriate colouring.
    """

    # Deduce the colours to use
    start = "\033[3;1m" if supports_color() else ""
    bold = "\033[3;1m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Prints the warning message with those colours
    print(f"{bold}[{end}{start}WARN{end}{bold}] {message}{end}", file=sys.stderr)





##### HELPER STRUCTS #####
class Arch:
    """
        Defines a class for keeping track of the target architecture.
    """

    _arch: str


    # Represents the AMD64 architecture.
    AMD64: Self = Self("amd64")
    # Represents the ARM64 architecture.
    ARM64: Self = Self("arm64")


    def __init__(self, arch: str):
        """
            Constructor for the Arch.

            # Arguments
            - `arch`: The string representation of the target architecture. Can be:
                - `x86_64` or `amd64` for Arch.Amd64; or
                - `aarch64` or `arm64` for Arch.Arm64.

            # Returns
            A new instance of Self.

            # Errors
            This function may eror if the input string was an invalid architecture.
        """

        # Attempt to parse it
        if arch == "x86_64" or arch == "amd64":
            self._arch = "amd64"
        elif arch == "aarch64" or arch == "arm64":
            self._arch = "arm64"
        else:
            raise ValueError(f"Invalid architecture string '{arch}'")

    def default():
        """
            Creates a default Arch matching the host's architecture.
        """

        if platform.machine().lower() == "x86_64" or platform.machine().lower() == "amd64":
            return Self("amd64")
        elif platform.machine().lower() == "arm64" or platform.machine().lower() == "aarch64":
            return Self("arm64")
        else:
            pwarn("Could not determine processor architecture; assuming x86-64 (specify it manually using '--arch' if incorrect)")


    def __str__(self) -> str:
        """
            Serializes the Arch for readability purposes.
        """

        if self._arch == "amd64":
            return "AMD64"
        elif self._arch == "arm64":
            return "ARM64"
        else:
            raise ValueError(f"Invalid internal architecture string '{self._arch}'")

    def brane(self) -> str:
        """
            Serializes the Arch for use in Brane executable names / other Brane executables.
        """

        if self._arch == "amd64":
            return "x86_64"
        elif self._arch == "arm64":
            return "aarch64"
        else:
            raise ValueError(f"Invalid internal architecture string '{self._arch}'")



class Os:
    def __init__(self, os: str):
        """
            Can be:
              - `win` or `windows` for Arch.WINDOWS;
              - `macos` or `darwin` for Arch.DARWIN; or
              - `linux` for Arch.LINUX.
        """

        pass





##### TARGET DEFINITIONS #####





##### TARGETS #####
TARGETS = {}






##### ENTRYPOINT #####





# Actual entrypoint
if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("TARGET", choices=list(TARGETS.keys()), help="The target to build.")

    parser.add_argument("--debug", action="store_true", help="If given, prints additional debug information to the output.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="If given, does not run anything but instead just reports what would've been run.")
    parser.add_argument("-a", "--arch", choices=["x86_64", "aarch64"], default=Arch.default(), help="Determines the architecture for which to download executables and such.")
    parser.add_argument("-o", "--os", choices=["win", "windows", "macos", "darwin", "linux"], default=Os.default(), help="Determines the operating system for which to download executables and such.")
