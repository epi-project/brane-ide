#!/usr/bin/env python3
# MAKE.py
#   by Lut99
#
# Created:
#   02 Aug 2023, 08:38:41
# Last edited:
#   17 Aug 2023, 15:51:18
# Auto updated?
#   Yes
#
# Description:
#   Make script for the Brane IDE project.
#

import abc
import argparse
import os
import pathlib
import platform
import shlex
import subprocess
import sys
import time
import typing


##### GLOBALS #####
# Determines if `pdebug()` does anything
DEBUG: bool = True

# Determines any arguments relevant only for targets
TARGET_ARGS: typing.Dict[str, typing.Any] = {}





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

def perror(message: str):
    """
        Prints an error message to stderr with appropriate colouring.
    """

    # Deduce the colours to use
    start = "\033[91;1m" if supports_color() else ""
    mid = "\033[1m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Prints the warning message with those colours
    print(f"{mid}[{end}{start}ERROR{end}{mid}] {message}{end}", file=sys.stderr)

def pwarn(message: str):
    """
        Prints a warning message to stderr with appropriate colouring.
    """

    # Deduce the colours to use
    start = "\033[3;1m" if supports_color() else ""
    mid = "\033[1m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Prints the warning message with those colours
    print(f"{mid}[{end}{start}WARN{end}{mid}] {message}{end}", file=sys.stderr)

def pdebug(message: str):
    """
        Prints a debug message to stderr with appropriate colouring.

        Note: only prints if the global `DEBUG` is set.
    """

    if DEBUG:
        # Deduce the colours to use
        start = "\033[90;1m" if supports_color() else ""
        mid = "\033[90m" if supports_color() else ""
        end = "\033[0m" if supports_color() else ""

        # Prints the warning message with those colours
        print(f"{mid}[{end}{start}DEBUG{end}{mid}] {message}{end}", file=sys.stderr)

def get_active_instance() -> typing.Optional[str]:
    """
        Returns the path to the active instance as indicated by Brane.

        Note that this function tightly integrates with brane-cli to find the active instance.

        Configuration directory location taken as brane_cli does, using https://docs.rs/dirs-2/latest/dirs_2/fn.config_dir.html.

        # Returns
        The path, or else `None` if we failed. The error is already printed as a warning, then.
    """

    # Expand the user path
    home = pathlib.Path.home()
    if Os.default() == Os.windows():
        config = f"{home}\\Appdata\\Roaming"
    elif Os.default() == Os.darwin():
        config = f"{home}/Library/Preferences"
    elif Os.default() == Os.linux():
        config = f"{home}/.config"
    else:
        raise ValueError(f"Unknown OS default '{Os.default()}'")
    brane = f"{config}/brane"

    # Check if it exists
    if not os.path.exists(brane):
        # Return the local directory instead
        pdebug(f"Brane configuration directory '{brane}' not found; assuming `brane` executable not used")
        return None

    # Attempt to find the active instance
    active = f"{brane}/active_instance"
    try:
        with open(active, "r") as h:
            active_instance = h.read()
    except FileNotFoundError:
        pwarn(f"Brane configuration directory exists, but no active instance found (run 'brane instance use ...' to make one active)")
        pdebug(f"Brane configuration directory: '{brane}'")
        pdebug(f"Expected location of active instance file: '{active}'")
        return None
    except IOError as e:
        pwarn(f"Failed to read active instance file '{active}': {e}")
        return None

    # Attempt to find that instance
    instances = f"{brane}/instances"
    instance = f"{instances}/{active_instance}"
    if not os.path.exists(instance):
        pwarn(f"Instance '{active_instance}' is currently marked as active instance, but no such instance found")
        return None

    # Otherwise yay
    return instance

def get_default_api_addr() -> str:
    """
        Attempts to get the currently active instance's API endpoint.

        If this fails, falls back to 'http://localhost:50051'.

        # Returns
        The path to the currently active certificate directory.
    """

    # Get the active instance's directory
    instance = get_active_instance()
    if instance is None:
        pdebug("Falling back to 'http://localhost:50051'")
        return "http://localhost:50051"

    # Attempt to read the YAML file with the info
    info = f"{instance}/info.yml"
    try:
        with open(info, "r") as h:
            info = h.read()
    except IOError as e:
        pwarn(f"Failed to read instance info file '{info}': {e}")
        pdebug("Falling back to 'http://localhost:50051'")
        return "http://localhost:50051"

    # Attempt to find the api address
    for line in info.splitlines():
        if len(line) >= 5 and line[:5] == "api: ":
            # We found it, mark whatever follows
            return line[5:]

    # Otherwise, not found
    pwarn(f"Instance info file '{info}' does not mention API address")
    pdebug("Falling back to 'http://localhost:50051'")
    return "http://localhost:50051"

def get_default_drv_addr() -> str:
    """
        Attempts to get the currently active instance's driver endpoint.

        If this fails, falls back to 'grpc://localhost:50053'.

        # Returns
        The path to the currently active certificate directory.
    """

    # Get the active instance's directory
    instance = get_active_instance()
    if instance is None:
        pdebug("Falling back to 'http://localhost:50053'")
        return "http://localhost:50053"

    # Attempt to read the YAML file with the info
    info = f"{instance}/info.yml"
    try:
        with open(info, "r") as h:
            info = h.read()
    except IOError as e:
        pwarn(f"Failed to read instance info file '{info}': {e}")
        pdebug("Falling back to 'http://localhost:50053'")
        return "http://localhost:50053"

    # Attempt to find the api address
    for line in info.splitlines():
        if len(line) >= 5 and line[:5] == "drv: ":
            # We found it, mark whatever follows
            return line[5:]

    # Otherwise, not found
    pwarn(f"Instance info file '{info}' does not mention driver address")
    pdebug("Falling back to 'http://localhost:50053'")
    return "http://localhost:50053"

def get_default_certs_dir() -> str:
    """
        Attempts to get the currently active certificate directory.

        If this fails, falls back to './certs'.

        # Returns
        The path to the currently active certificate directory.
    """

    # Get the active instance's directory
    instance = get_active_instance()
    if instance is None:
        pdebug("Falling back to './certs'")
        return "./certs"

    # If we found it, mark its directory!
    return f"{instance}/certs"





##### HELPER STRUCTS #####
T = typing.TypeVar("T")

class ResolveArgs(typing.Generic[T]):
    """
        "Generics function" that resolves a given string value in the `TARGET_ARGS` dictionary if it starts with a dollar sign (`$`).

        # Arguments
        - `key`: The key to resolve.

        # Returns
        Either the key if it did not start with a dollar sign, or else the resolved value casted to type `T`.
    """

    def __call__(self, key: str) -> typing.Union[str, T]:
        """
            "Generics function" that resolves a given string value in the `TARGET_ARGS` dictionary if it starts with a dollar sign (`$`).

            # Arguments
            - `key`: The key to resolve.

            # Returns
            Either the key if it did not start with a dollar sign, or else the resolved value casted to type `T`.
        """

        # See if it starts with the all-important dollar
        if len(key) == 0 or key[0] != '$': return key
        key = key[1:]

        # Else, resolve to the value
        if key not in TARGET_ARGS: raise KeyError(f"Unknown key '{key}' in TARGET_ARGS")
        value = TARGET_ARGS[key]

        # Return it as the target type
        return value



class Arch:
    """
        Defines a class for keeping track of the target architecture.
    """

    _arch: str


    # Represents the AMD64 architecture.
    AMD64: str = "amd64"
    # Represents the ARM64 architecture.
    ARM64: str = "arm64"


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
        try:
            self._arch = self.allowed()[arch]
        except KeyError:
            raise ValueError(f"Invalid architecture string '{arch}'")

    @staticmethod
    def default():
        """
            Creates a default Arch matching the host's architecture.
        """

        if platform.machine().lower() == "x86_64" or platform.machine().lower() == "amd64":
            return Arch(Arch.AMD64)
        elif platform.machine().lower() == "arm64" or platform.machine().lower() == "aarch64":
            return Arch(Arch.ARM64)
        else:
            pwarn("Could not determine processor architecture; assuming x86-64 (specify it manually using '--arch' if incorrect)")
            return Arch(Arch.AMD64)

    @staticmethod
    def amd64():
        """
            Constructor for an x86-64 architecture.

            Shorthand for: `Arch(Arch.AMD64)`.

            # Returns
            A new instance of Self that refers to an x86-64 / AMD64 architecture.
        """

        return Arch(Arch.AMD64)
    @staticmethod
    def arm64():
        """
            Constructor for an ARM 64-bit architecture.

            Shorthand for: `Arch(Arch.ARM64)`.

            # Returns
            A new instance of Self that refers to a 64-bit ARM architecture.
        """

        return Arch(Arch.ARM64)

    def __eq__(self, other: typing.Any) -> bool:
        if type(self) == type(other):
            return self._arch == other._arch
        else:
            return False
    def __str__(self) -> str:
        """
            Serializes the Arch for readability purposes.
        """

        if self._arch == Arch.AMD64:
            return "AMD64"
        elif self._arch == Arch.ARM64:
            return "ARM64"
        else:
            raise ValueError(f"Invalid internal architecture string '{self._arch}'")

    def brane(self) -> str:
        """
            Serializes the Arch for use in Brane executable names / other Brane executables.
        """

        if self._arch == Arch.AMD64:
            return "x86_64"
        elif self._arch == Arch.ARM64:
            return "aarch64"
        else:
            raise ValueError(f"Invalid internal architecture string '{self._arch}'")
    def docker(self) -> str:
        """
            Serializes the Arch for use in Docker commands.
        """

        if self._arch == Arch.AMD64:
            return "amd64"
        elif self._arch == Arch.ARM64:
            return "arm64"
        else:
            raise ValueError(f"Invalid internal architecture string '{self._arch}'")

    @staticmethod
    def allowed() -> typing.Dict[str, str]:
        """
            Returns a mapping of all inputs to output architectures.

            # Returns
            A map of valid string representations mapping to output `Arch`s.
        """

        return {
            "x86_64" : Arch.AMD64,
            "amd64"  : Arch.AMD64,

            "aarch64" : Arch.ARM64,
            "arm64"   : Arch.ARM64,
        }

class Os:
    """
        Defines a class for keeping track of the target operating system.
    """

    _os: str


    # Represents Windows.
    WINDOWS: str = "windows"
    # Represents macOS.
    DARWIN: str = "darwin"
    # Represents Linux.
    LINUX: str = "linux"


    def __init__(self, os: str):
        """
            Constructor for the OS.

            # Arguments
            - `os`: The string representation of the target operating system. Can be:
                - `win` or `windows` for Os.WINDOWS;
                - `macos` or `darwin` for Os.DARWIN; or
                - `linux` for Os.LINUX.

            # Returns
            A new instance of Self.

            # Errors
            This function may eror if the input string was an invalid operating system.
        """

        # Attempt to parse it
        try:
            self._os = self.allowed()[os]
        except KeyError:
            raise ValueError(f"Invalid operating system string '{os}'")

    @staticmethod
    def default():
        """
            Creates a default OS matching the host's architecture.
        """

        if platform.system().lower() == "windows":
            return Os(Os.WINDOWS)
        elif platform.system().lower() == "darwin":
            return Os(Os.DARWIN)
        elif platform.system().lower() == "linux":
            return Os(Os.LINUX)
        else:
            pwarn("Could not determine operating system; assuming Linux (specify it manually using '--os' if incorrect)")
            return Os(Os.LINUX)

    @staticmethod
    def windows():
        """
            Constructor for a Windows operating system.

            Shorthand for: `Os(Os.WINDOWS)`.

            # Returns
            A new instance of Self that refers to Windows.
        """

        return Os(Os.WINDOWS)
    @staticmethod
    def darwin():
        """
            Constructor for a macOS (Darwin) operating system.

            Shorthand for: `Os(Os.DARWIN)`.

            # Returns
            A new instance of Self that refers to macOS.
        """

        return Os(Os.DARWIN)
    @staticmethod
    def linux():
        """
            Constructor for a Linux operating system.

            Shorthand for: `Os(Os.LINUX)`.

            # Returns
            A new instance of Self that refers to Linux.
        """

        return Os(Os.LINUX)

    def __eq__(self, other: typing.Any) -> bool:
        if type(self) == type(other):
            return self._os == other._os
        else:
            return False
    def __str__(self) -> str:
        """
            Serializes the OS for readability purposes.
        """

        if self._os == Os.WINDOWS:
            return "Windows"
        elif self._os == Os.DARWIN:
            return "macOS"
        elif self._os == Os.LINUX:
            return "Linux"
        else:
            raise ValueError(f"Invalid internal operating system string '{self._os}'")

    def brane(self) -> str:
        """
            Serializes the OS for use in Brane executable names / other Brane executables.
        """

        if self._os == Os.WINDOWS:
            return "win"
        elif self._os == Os.DARWIN:
            return "darwin"
        elif self._os == Os.LINUX:
            return "linux"
        else:
            raise ValueError(f"Invalid internal operating system string '{self._os}'")
    def docker(self) -> str:
        """
            Serializes the OS for use in Docker commands.
        """

        if self._os == Os.WINDOWS:
            return "windows"
        elif self._os == Os.DARWIN:
            return "darwin"
        elif self._os == Os.LINUX:
            return "linux"
        else:
            raise ValueError(f"Invalid internal operating system string '{self._os}'")

    @staticmethod
    def allowed() -> typing.Dict[str, str]:
        """
            Returns a mapping of all inputs to output operating systems.

            # Returns
            A map of valid string representations mapping to output `Os`s.
        """

        return {
            "win"     : Os.WINDOWS,
            "windows" : Os.WINDOWS,

            "macos"  : Os.DARWIN,
            "darwin" : Os.DARWIN,

            "linux" : Os.LINUX,
        }



class Process:
    """
        Builds an abstraction over a subprocess that is useful to us.
    """

    exe  : str
    args : typing.List[str]
    env  : typing.Dict[str, str]

    _stdout : bool
    _stderr : bool


    def __init__(self, exe: typing.Union[str, typing.List[str]], *args: str, env: typing.Dict[str, str] = dict(os.environ), capture_stdout: bool = False, capture_stderr: bool = False):
        """
            Constructor for the Process.

            # Arguments
            - `exe`: The executable to run (i.e., first argument).
            - `args`: Any other arguments.
            - `env`: The environment to set for this Process. Copies the script's environment by default.
            - `capture_stdout`: Whether to capture stdout (True) or simply write to this process' stdout.
            - `capture_stderr`: Whether to capture stderr (True) or simply write to this process' stderr.

            # Returns
            A new instance of a Process.
        """

        # Build the process
        if type(exe) == str:
            self.exe  = exe
            self.args = list(args)
        elif type(exe) == list:
            self.exe  = exe[0]
            self.args = exe[1:]
        else:
            raise TypeError(f"Illegal type '{type(exe)}' for exe")
        self.env  = env

        self._stdout = capture_stdout
        self._stderr = capture_stderr

    def add_arg(self, *args: str):
        """
            Adds additional arguments.
        """

        self.args += list(args)

    def execute(self, dry_run: bool, show_cmd: bool = True) -> typing.Tuple[int, typing.Optional[str], typing.Optional[str]]:
        """
            Executes the process.

            # Arguments
            - `dry_run`: If True, does not actually run the command but returns a bogus (0, "", "") (or None if applicable)
            - `show_cmd`: Whether to print the command we're executing to the stdout/stderr or not.

            # Returns
            A tuple with:
            - The exit code of the process.
            - The captured stdout (if capture_stdout was True; otherwise, `None` is returned)
            - The captured stderr (if capture_stderr was True; otherwise, `None` is returned)

            # Errors
            This function will raise an exception if we failed to run the process in the first place.
        """

        # Print the thing if desired
        args = [ self.exe ] + self.args
        if show_cmd:
            bold = "\033[1m" if supports_color() else ""
            end = "\033[0m" if supports_color() else ""
            print(f"{bold} > {Process.shellify(args)}{end}")

        # Run the argument if not dry_run
        if not dry_run:
            handle = subprocess.Popen(args, env=self.env, stdout=(subprocess.PIPE if self._stdout else sys.stdout), stderr=(subprocess.PIPE if self._stderr else sys.stderr))
            (stdout, stderr) = handle.communicate()
            return (handle.returncode, stdout.decode() if self._stdout else None, stderr.decode() if self._stderr else None)
        else:
            # Return dummy values
            return (0, "" if self._stdout else None, "" if self._stderr else None)

    @staticmethod
    def shellify(args: typing.List[str]) -> str:
        """
            Converts a list of arguments to a shell-like string.
        """

        return ' '.join([ (f"\"{a}\"" if ' ' in a else f"{a}") for a in args ])



class ExtractMethod(abc.ABC):
    """
        Virtual class for all possible log extraction methods.
    """

    def __init__(self):
        # Nothing to be done
        pass

    @abc.abstractmethod
    def extract(self, haystack: str) -> typing.Optional[str]:
        """
            Extracts the interested area from the given text and returns it.

            # Arguments
            - `haystack`: The text to extract from.

            # Returns
            The extract part of the `haystack`.
        """

        pass

class ConsecutiveExtract(ExtractMethod):
    """
        Applies multiple Extracts, each to the result of the previous.
    """

    _extracts : typing.List[ExtractMethod]


    def __init__(self, extracts: typing.List[ExtractMethod]):
        """
            Constructor for the ConsecutiveExtract.

            # Arguments
            - `extracts`: The list of extracts to consecutively apply.

            # Returns
            A new instance of a ConsecutiveExtract.
        """

        # initialize super
        super().__init__()

        # Set the extracts
        self._extracts = extracts

    def extract(self, haystack: str) -> typing.Optional[str]:
        """
            Extracts the interested area from the given text and returns it.

            # Arguments
            - `haystack`: The text to extract from.

            # Returns
            The extract part of the `haystack`.
        """

        # Apply them as long as we can
        for ext in self._extracts:
            narrowed_haystack = ext.extract(haystack)
            if narrowed_haystack is None: return None
            haystack = narrowed_haystack
        return haystack

class MatchedLineExtract(ExtractMethod):
    """
        Matches the first line that contains the given substring.
    """

    _substr : str
    _nth: int


    def __init__(self, substring: str, nth: int = 0):
        """
            Constructor for the MatchedLineExtract.

            # Arguments
            - `substring`: The first line containing this as a substring is returned.
            - `nth`: How manieth match to take. By default, means the first one. Can use -1 to mean the last, -2 to mean the second-to-last, etc.

            # Returns
            A new instance of a MatchedLineExtract.
        """

        # initialize super
        super().__init__()

        # Set out own parameters
        self._substr = substring
        self._nth = nth

    def extract(self, haystack: str) -> typing.Optional[str]:
        """
            Extracts the interested area from the given text and returns it.

            # Arguments
            - `haystack`: The text to extract from.

            # Returns
            The extract part of the `haystack`.
        """

        # Return the line that has the substring
        n_matches = 0
        for line in haystack.splitlines():
            if self._substr in line:
                if n_matches == self._nth: return line
                n_matches += 1

        # Else, return None
        return None

class MatchNthWordExtract(ExtractMethod):
    """
        Matches only the nth word in the given input.
    """

    _n : int


    def __init__(self, n: int):
        """
            Constructor for the MatchNthWordExtract.

            # Arguments
            - `n`: Gives the meaning to "n" in "The n'th word to match" (zero-indexed).

            # Returns
            A new instance of a MatchNthWordExtract.
        """

        # initialize super
        super().__init__()

        # Set out own parameters
        self._n = n

    def extract(self, haystack: str) -> typing.Optional[str]:
        """
            Extracts the interested area from the given text and returns it.

            # Arguments
            - `haystack`: The text to extract from.

            # Returns
            The extract part of the `haystack`.
        """

        # Return the nth word
        for (i, word) in enumerate(haystack.split()):
            if i == self._n: return word
        # Else, return None
        return None





##### TARGET DEFINITIONS #####
class Target(abc.ABC):
    """
        Defines the common ancestor for all targets in this make script.
    """

    id   : str
    deps : typing.List[str]
    desc : str


    def __init__(self, id: str, dependencies: typing.List[str] = [], description: str = ""):
        """
            Initializes the common ancestor of all targets.

            # Arguments
            - `id`: The string identifier for this target.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.
        """

        self.id = id
        self.deps = dependencies
        self.desc = description

    @abc.abstractmethod
    def build(self, arch: Arch, os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        pass

    @abc.abstractmethod
    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        pass



class ArrayTarget(Target):
    """
        Target that runs multiple various other targets in succession.

        This can be modelled with dependencies too, but this target is here to reduce the target count.
    """

    _targets : typing.List[Target]


    def __init__(self, id: str, targets: typing.List[Target], deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the ArrayTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `targets`: A list of targets to run.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new ArrayTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Set the commands
        self._targets = targets

    def build(self, arch: Arch, os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Simply build them all in-order
        changed = False
        for target in self._targets:
            pdebug(f"Building child target '{target.id}' of target '{self.id}'")
            changed = changed or target.build(arch, os, dry_run)
        return changed

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Simply check for outdatedness in-order
        for target in self._targets:
            if target.is_outdated():
                pdebug(f"Marking target '{self.id}' as outdated because child target '{target.id}' is outdated")
                return True
        pdebug("Marking target '{}' as up-to-date because all child targets ({}) are up-to-date".format(self.id, ", ".join([ f"'{t.id}'" for t in self._targets ])))
        return False

class MakeDirTarget(Target):
    """
        Target that creates a directory using Python's API.
    """

    _path : str
    _all  : bool


    def __init__(self, id: str, path: str, make_all: bool = True, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the MakeDirTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `path`: The path of the directory to construct.
            - `make_all`: If true, also creates missing parent directories.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new MakeDirTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Set the commands
        self._path = path
        self._all = make_all

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Determine colours to use
        bold = "\033[1m" if supports_color() else ""
        end  = "\033[0m" if supports_color() else ""

        # Resolve the path
        path = ResolveArgs[str]()(self._path)

        # Create the directory(s)
        print(f"{bold} > Creating directory '{path}'...{end}")
        if not dry_run:
            if self._all:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Resolve the path
        path = ResolveArgs[str]()(self._path)

        # Check only if it exists
        if not os.path.exists(path):
            pdebug(f"Marking target '{self.id}' as outdated because to-be-created directory '{path}' does not exist")
            return True
        else:
            pdebug(f"Marking target '{self.id}' as up-to-date because to-be-created directory '{path}' already exists")
            return False

class CopyFileTarget(Target):
    """
        Copies a file from one location to another.
    """

    _source   : str
    _target   : str
    _fix_dirs : bool


    def __init__(self, id: str, source: str, target: str, fix_dirs: bool = True, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the CopyFileTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `source`: The source location to copy _from_.
            - `target`: The target location to copy _to_.
            - `fix_dirs`: Determines if we need to generate missing directories before copying or not.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Set the child fields
        self._source = source
        self._target = target
        self._fix_dirs = fix_dirs

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Determine colours to use
        bold = "\033[1m" if supports_color() else ""
        end  = "\033[0m" if supports_color() else ""

        # Resolve the source & targets
        source = ResolveArgs[str]()(self._source)
        target = ResolveArgs[str]()(self._target)

        # Attempt to fix directories if missing
        if self._fix_dirs:
            parent = pathlib.Path(target).parent
            if not os.path.exists(parent):
                print(f"{bold} > Creating parent directory '{parent}'...{end}")
                if not dry_run: os.makedirs(parent)

        # Open the file, write buffered
        print(f"{bold} > Copying '{source}' to '{target}'...{end}")
        if not dry_run:
            with open(source, "rb") as s:
                with open(target, "wb") as f:
                    while True:
                        # Read from the source
                        buffer = s.read(65535)
                        if len(buffer) == 0: break

                        # Write to the target
                        f.write(buffer)
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Resolve the source & targets
        source = ResolveArgs[str]()(self._source)
        target = ResolveArgs[str]()(self._target)

        # First check if the target exists
        if not os.path.exists(target):
            pdebug(f"Marking target '{self.id}' as outdated because the copy target '{target}' does not exist")
            return True

        # Next, compute a quick hash of the source and target to see if we need to copy
        with open(source, "rb") as s:
            source_hash = hash(s.read())
        with open(target, "rb") as t:
            target_hash = hash(t.read())
        if source_hash != target_hash:
            pdebug(f"Marking target '{self.id}' as outdated because source hash '{hex(source_hash)}' does not match target hash '{hex(target_hash)}'")
            return True

        # Otherwise, nothing needs to happen
        pdebug(f"Marking target '{self.id}' as up-to-date because the target '{target}' exists and its hash matches that of the source '{source}'")
        return False

class ImageTarget(Target):
    """
        Builds a Docker image.
    """

    _image   : str
    _file    : str
    _context : str
    _target  : typing.Optional[str]
    _args    : typing.Dict[str, str]


    def __init__(self, id: str, image: str, file: str = "./Dockerfile", context: str = ".", target: typing.Optional[str] = None, build_args: typing.Dict[str, str] = {}, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the ImageTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `image`: The name of the image to build.
            - `file`: The Dockerfile to build.
            - `context`: The folder context to build.
            - `target`: The target to build in the image. If omitted, builds the default target.
            - `build_args`: Any build arguments to set. Note that 'ARCH' and 'OS' are set automatically.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new ImageTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._image   = image
        self._file    = file
        self._context = context
        self._target  = target
        self._args    = build_args

    def build(self, arch: Arch, os_: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Construct the Docker arguments
        args = typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "build", "--load", "-t", self._image ]
        if self._target is not None:
            args += [ "--target", self._target ]
        for arg in self._args:
            args += [ "--build-arg", f"{arg}={self._args[arg]}" ]
        if arch != Arch.default() or os_ != Os.default():
            args += [ "--platform", f"{os_.docker()}/{arch.docker()}" ]
        args += [ "-f", self._file, "." ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])

        # Run the process
        (code, _, _) = Process(args, env=env).execute(dry_run)
        if code != 0:
            raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")

        # Alright done!
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # # Collect the list of available images
        # pdebug(f"Checking if an image named '{self._image}' exists...")
        # env = dict(os.environ)
        # env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        # (code, stdout, _) = Process(TARGET_ARGS['docker'] + [ "image", "list" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        # if code != 0: raise RuntimeError(f"Failed to run command to check if image '{self._image}' is running")

        # # We are only outdated if it does not exist
        # if self._image in stdout:
        #     pdebug(f"Marking target '{self.id}' as up-to-date because image '{self._image}' already exists")
        #     return False
        # else:
        #     pdebug(f"Marking target '{self.id}' as outdated because no image '{self._image}' is found")
        #     return True

        # Simply always build because we are not tracking files ourselves
        pdebug(f"Marking target '{self.id}' as outdated because image targets are always built (to have docker deal with cache staleness)")
        return True

class RunContainerTarget(Target):
    """
        Starts a Docker container.
    """

    _name       : str
    _image      : str
    _args       : typing.List[str]
    _entrypoint : typing.Optional[str]
    _commands   : typing.Optional[str]
    _volumes    : typing.List[typing.Tuple[str, str]]


    def __init__(self, id: str, name: str, image: str, args: typing.List[str] = [], entrypoint: typing.Optional[str] = None, commands: typing.Optional[str] = None, volumes: typing.List[typing.Tuple[str, str]] = [], deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RunContainerTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `name`: The name of the to-be-started container.
            - `args`: Any additional runtime arguments.
            - `image`: The name of the image to start.
            - `entrypoint`: If not None, overrides the ENTRYPOINT set in the image.
            - `commands`: If not None, overrides the image's CMD.
            - `volumes`: Any volumes to attach. Given as tuple of (host, container) paths.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new RunContainerTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._name       = name
        self._image      = image
        self._args       = args
        self._entrypoint = entrypoint
        self._commands   = commands
        self._volumes    = volumes

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Collect the list of available images
        pdebug(f"Checking if a container named '{self._name}' exists...")
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])
        (code, stdout, _) = Process(typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "ps", "-a" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' is running")
        if stdout is None: raise RuntimeError(f"Expected non-empty 'stdout', got empty 'stdout'")

        # Remove the container if it exists
        if self._name in stdout:
            pdebug(f"Removing existing container '{self._name}'...")
            (code, _, _) = Process(typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "rm", "-f", self._name ], capture_stdout=True).execute(dry_run)
            if code != 0: raise RuntimeError(f"Failed to run command to remove container '{self._name}'")

        # Construct the Docker arguments
        args = typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "run", "-d", "--name", self._name ]
        for host, cont in self._volumes:
            args += [ "-v", f"{host}:{cont}" ]
        if self._entrypoint is not None:
            args += [ "--entrypoint", self._entrypoint ]
        if self._commands is not None:
            args += [ "--cmd", self._commands ]
        args += [ self._image ] + self._args

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])

        # Run the process
        (code, _, _) = Process(args, env=env).execute(dry_run)
        if code != 0:
            raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")

        # Alright done!
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Collect the list of available images
        pdebug(f"Checking if a container named '{self._name}' is running...")
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])
        (code, stdout, _) = Process(typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "ps" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' is running")
        if stdout is None: raise RuntimeError(f"Expected non-empty 'stdout', got empty 'stdout'")

        # If it contains the target container we are happy
        if self._name in stdout:
            pdebug(f"Marking target '{self.id}' as up-to-date because a running container is found")
            return False
        else:
            pdebug(f"Marking target '{self.id}' as outdated because no running container is found")
            return True

class RunComposeTarget(Target):
    """
        Starts a Docker Compose file.
    """

    _file      : str
    _namespace : typing.Optional[str]
    _env       : typing.Dict[str, str]


    def __init__(self, id: str, file: str, namespace: typing.Optional[str] = None, env: typing.Dict[str, str] = dict(os.environ), deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RunComposeTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `file`: The Docker Compose-file to run.
            - `namespace`: Any project/namespace to set for this run. Can be `None` to stick to compose's default.
            - `env`: Any additional environment variables to set for the run.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new RunComposeTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._file      = file
        self._namespace = namespace
        self._env       = env

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Create the arguments
        args = typing.cast(typing.List[str], TARGET_ARGS["docker_compose"])
        if self._namespace is not None:
            args += [ "-p", self._namespace ]
        args += [ "-f", self._file, "up", "-d" ]

        # Resolve the environment by adding DOCKER_SOCKET and by resolving TARGET_ARGS
        for key in self._env:
            self._env[key] = ResolveArgs[str]()(self._env[key])
        self._env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])

        # Run the process
        (code, _, _) = Process(args, env=self._env).execute(dry_run)
        if code != 0:
            raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")

        # Alright done!
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Never outdated
        pdebug(f"Marking target '{self.id}' as outdated because compose targets are always outdated")
        return True

class RmContainerTarget(Target):
    """
        Removes a running Docker container.
    """

    _name  : str
    _force : bool


    def __init__(self, id: str, name: str, force: bool = False, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RmContainerTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `name`: The name of the to-be-removed container.
            - `force`: Whether the container should still be removed if it's running.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new RmContainerTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._name  = name
        self._force = force

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Build the command
        args = typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "rm" ]
        if self._force:
            args += [ "-f" ]
        args += [ self._name ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])

        # Run it
        (code, _, _) = Process(args, env=env).execute(dry_run)
        if code != 0: raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")

        # Alright done
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Collect the list of available images
        pdebug(f"Checking if a container named '{self._name}' exists...")
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])
        (code, stdout, _) = Process(typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "ps", "-a" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' exists")
        if stdout is None: raise RuntimeError(f"Expected non-empty 'stdout', got empty 'stdout'")

        # If it contains the target container we are happy
        if self._name in stdout:
            pdebug(f"Marking target '{self.id}' as outdated because container '{self._name}' exists")
            return True
        else:
            pdebug(f"Marking target '{self.id}' as up-to-date because container '{self._name}' does not exist")
            return False

class RmComposeTarget(Target):
    """
        Removes a running Docker Compose project.
    """

    _file      : str
    _namespace : typing.Optional[str]
    _env       : typing.Dict[str, str]


    def __init__(self, id: str, file: str, namespace: typing.Optional[str] = None, env: typing.Dict[str, str] = dict(os.environ), deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RmComposeTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `file`: The Docker Compose-file to run.
            - `namespace`: Any project/namespace to set for this run. Can be `None` to stick to compose's default.
            - `env`: Any environment variables to set. This is mostly here to keep Docker Compose happy and populate proper envs in the file.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new RmComposeTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._file      = file
        self._namespace = namespace
        self._env       = env

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Build the command
        args = typing.cast(typing.List[str], TARGET_ARGS["docker_compose"])
        if self._namespace is not None:
            args += [ "-p", self._namespace ]
        args += [ "-f", self._file, "down" ]

        # Resolve the environment by adding DOCKER_SOCKET and by resolving TARGET_ARGS
        for key in self._env:
            self._env[key] = ResolveArgs[str]()(self._env[key])
        self._env["DOCKER_SOCKET"] = typing.cast(str, TARGET_ARGS["docker_socket"])

        # Run it
        (code, _, _) = Process(args, env=self._env).execute(dry_run)
        if code != 0: raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")

        # Alright done
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Never outdated
        pdebug(f"Marking target '{self.id}' as outdated because compose targets are always outdated")
        return True

class ExtractContainerLogsTarget(Target):
    """
        Target that extracts a specific part of the logs of a Docker container.
    """

    _cont    : str
    _msg     : str
    _extract : ExtractMethod
    _strip   : bool
    _timeout : float


    def __init__(self, id: str, container: str, message: str, extract: ExtractMethod, strip: bool = False, timeout: float = 0, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the ExtractContainerLogsTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `container`: The container to extract the logs from.
            - `message`: The message to show above the extracted log(s).
            - `extract`: The extraction method to apply.
            - `strip`: If True, strips the extracted text of whitelines at both ends before printing it.
            - `timeout`: Any time to wait before extracting the information from the logs. The message _is_ already printed. Given as seconds.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new ExtractContainerLogsTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Set the extraction method and other properties
        self._cont = container
        self._msg = message
        self._extract = extract
        self._strip = strip
        self._timeout = timeout

    def build(self, _arch: Arch, _os: Os, dry_run: bool) -> bool:
        """
            Builds this target.

            # Arguments
            - `arch`: The `Arch` that describes the architecture to build for.
            - `os`: The `Os` that describes the operating system to build for.
            - `dry_run`: If True, does not run any commands but just says it would.

            # Returns
            Whether any changes to relevant output were triggered.
        """

        # Show the message
        print(f"{self._msg}")

        # Wait if a timeout is given
        if self._timeout > 0:
            time.sleep(self._timeout)

        # Attempt to get the container's logs
        args = typing.cast(typing.List[str], TARGET_ARGS["docker"]) + [ "logs", self._cont ]
        (code, stdout, stderr) = Process(args, capture_stdout=True, capture_stderr=True).execute(dry_run, show_cmd=False)
        if code != 0:
            raise RuntimeError(f"Failed to run command '{Process.shellify(args)}'")
        if stdout is None: raise RuntimeError(f"Expected non-empty 'stdout', got empty 'stdout'")
        if stderr is None: raise RuntimeError(f"Expected non-empty 'stderr', got empty 'stderr'")

        # Find the extracted part
        extracted = self._extract.extract(stdout + "\n" + stderr)
        if extracted is None:
            raise RuntimeError(f"Cannot extract container '{self._cont}' logs")
        if self._strip:
            extracted = extracted.strip()

        # Show it
        print('\n'.join([ f"    {l}" for l in extracted.splitlines() ]))
        print("")

        # We say nothing happened because we didn't influence anything
        return False

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Extract targets are always outdated
        pdebug(f"Marking target '{self.id}' as outdated because log extraction targets are always outdated")
        return True





##### TARGETS #####
TARGETS: typing.Dict[str, Target] = { t.id: t for t in [
    ### IMAGES ###
    ImageTarget("dev-image",
        "brane-ide-dev",
        target="dev",
        description="Builds the development image for the Brane IDE project."
    ),
    ImageTarget("run-image",
        "brane-ide-server",
        target="run",
        description="Builds the runtime image for the Brane IDE project."
    ),

    ### SHELL TARGETS ###
    ArrayTarget("prepare-start-ide",
        [
            MakeDirTarget("mkdir-notebook", "$brane_notebook_dir"),
            MakeDirTarget("mkdir-data", "$brane_data_dir"),
            MakeDirTarget("mkdir-certs", "$brane_certs_dir"),
        ],
        description="Prepares starting the IDE by creating the attached folders."
    ),
    CopyFileTarget("libbrane_cli",
        "$libbrane_cli",
        ".tmp/libbrane_cli.so",
        description="Copies the `libbrane_cli.so` shared library to a container-accessible location."
    ),

    ### USER TARGETS ###
    RunContainerTarget("start-dev",
        "brane-ide-dev",
        "brane-ide-dev",
        volumes=[(".", "/source")],
        entrypoint="sleep",
        args=[ "infinity" ],
        deps=["dev-image"],
        description="Launches the development image for the Brane IDE project. You can connect in this with VS Code's Remote Development extension to access all dependencies."
    ),
    RmContainerTarget("stop-dev",
        "brane-ide-dev",
        force=True,
        description="Stops the development image for the Brane IDE project if it is running, and then removes it."
    ),

    RunComposeTarget("start-ide-quiet",
        "./docker-compose.yml",
        namespace="brane-ide",
        deps=["libbrane_cli", "run-image", "prepare-start-ide"],
        env={
            **dict(os.environ),
            **{
                "DEBUG": "$debug",
                "BRANE_API_URL": "$brane_api",
                "BRANE_DRV_URL": "$brane_drv",
                "BRANE_DATA_DIR": "$brane_data_dir",
                "BRANE_CERTS_DIR": "$brane_certs_dir",
                "BRANE_NOTEBOOK_DIR": "$brane_notebook_dir",
            }
        },
        description="Starts the runtime image for the Brane IDE project without querying the token."
    ),
    ExtractContainerLogsTarget("start-ide",
        "brane-ide",
        "JupyterLab launched at:",
        ConsecutiveExtract([ MatchedLineExtract("lab?token=", nth=1), MatchNthWordExtract(4) ]),
        strip = True,
        deps=["start-ide-quiet"],
        description="Starts the runtime image for the Brane IDE project without querying the token."
    ),
    RmComposeTarget("stop-ide",
        "./docker-compose.yml",
        namespace="brane-ide",
        env={
            **dict(os.environ),
            **{
                "DEBUG": "$debug",
                "BRANE_API_URL": "$brane_api",
                "BRANE_DRV_URL": "$brane_drv",
                "BRANE_DATA_DIR": "$brane_data_dir",
                "BRANE_CERTS_DIR": "$brane_certs_dir",
                "BRANE_NOTEBOOK_DIR": "$brane_notebook_dir",
            }
        },
        description="Stops the runtime image for the Brane IDE project if it is running, and then removes it."
    ),
] }





##### LIBRARY #####
def build(target: Target, arch: Arch, os: Os, force: bool, dry_run: bool):
    """
        Builds a given targets and its dependencies.

        Actually, recursively builds the target's dependencies first.

        # Arguments
        - `target`: The `Target` to build.
        - `arch`: The `Arch` that describes the architecture to build for.
        - `os`: The `Os` that describes the operating system to build for.
        - `force`: If given, forces rebuild of everything regardless of whether it wants to be rebuild.
        - `dry_run`: If True, does not run any commands but just says it would.

        # Returns
        Whether the build caused any (significant) changes.
    """

    # Determines some terminal colours
    green = "\033[92;1m" if supports_color() else ""
    bold = "\033[1m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Build the dependencies, first
    changed = force
    pdebug(f"Target '{target.id}' dependencies: {','.join([ d for d in target.deps ]) if len(target.deps) > 0 else '<none>'}")
    for dep in target.deps:
        # Get it as a target
        dep_target = TARGETS[dep]

        # Build it recursively
        dep_changed = build(dep_target, arch, os, force, dry_run)
        if not force and dep_changed: pdebug(f"Marking target '{target.id}' as outdated because its dependency '{dep}' was outdated")

        # Update the changed status
        changed = changed or dep_changed

    # Check if the target itself needs updating
    if force: pdebug(f"Marking target '{target.id}' as outdated because '--force' is given")
    changed = changed or target.is_outdated()

    # Build the target itself if it wants to be built
    if changed:
        print(f"{bold}Building target {end}{green}{target.id}{end}{bold}...{end}")
        target.build(arch, os, dry_run)
    else:
        pdebug(f"Not building target '{target.id}' because it is not marked as outdated")

    # Done, return whether anything was changed for downstream dependencies
    return changed





##### ENTRYPOINT #####
def main(targets: typing.List[str], arch: Arch, os: Os, force: bool, dry_run: bool) -> int:
    """
        Entrypoint function for the script.

        # Arguments
        - `targets`: The targets to build.
        - `arch`: The architecture to build for.
        - `os`: The operating system to build for.
        - `force`: If given, forces rebuild of everything regardless of whether it wants to be rebuild.
        - `dry_run`: If given, only emits what it is doing and doesn't actually do it.

        # Returns
        The script exit code.
    """

    # Deduce some colours
    red = "\033[91;1m" if supports_color() else ""
    bold = "\033[1m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Print intro if given
    pdebug( "`make.py` called with:")
    pdebug( " - targets       : {}".format(', '.join([ f"'{t}'" for t in targets ])))
    pdebug(f" - arch          : {arch}")
    pdebug(f" - os            : {os}")
    pdebug(f" - force         : {force}")
    pdebug(f" - dry_run       : {dry_run}")
    pdebug( "")
    pdebug( "Target arguments:")
    for arg in TARGET_ARGS:
        pdebug(f" - {arg}: {TARGET_ARGS[arg]}")
    if DEBUG: print()

    # Build all targets
    for target in targets:
        if target not in TARGETS:
            if not DEBUG: print(file=sys.stderr)
            perror(f"Unknown target '{target}'")
            print(file=sys.stderr); return 1
        build_target = TARGETS[target]

        # Run the build
        try:
            build(build_target, arch, os, force, dry_run)

        except Exception as e:
            print(file=sys.stderr)
            perror(f"{bold}Failed to build target {end}{red}{target}{end}{bold}:{end}")
            print(f"{e}", file=sys.stderr)
            print(file=sys.stderr)
            return 1

    # Done!
    return 0;



def list_targets() -> int:
    """
        Alternative entrypoint that just lists the targets in the TARGETS dict.
    """

    # Assign colours, if any
    green = "\033[92;1m" if supports_color() else ""
    dim = "\033[90m" if supports_color() else ""
    end = "\033[0m" if supports_color() else ""

    # Print everything
    print("Supported targets:")
    sorted_keys = list(TARGETS); sorted_keys.sort()
    for id in sorted_keys:
        print(f"{dim} - {end}{green}{id}{end}{dim}:{end} {TARGETS[id].desc}")

    # Sweet, done
    return 0





# Actual entrypoint
if __name__ == "__main__":
    # Define the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("TARGETS", nargs='*', help="The target(s) to build. See '--targets' for how to obtain a list of valid targets.")

    parser.add_argument("-t", "--targets", action="store_true", help="If given, prints the list of supported targets and then quits.")

    parser.add_argument("--debug", action="store_true", help="If given, prints additional debug information to the output.")
    parser.add_argument("-f", "--force", action="store_true", help="If given, forces rebuild of everything regardless of whether it wants to be rebuild.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="If given, does not run anything but instead just reports what would've been run.")
    parser.add_argument("-a", "--arch", choices=Arch.allowed().keys(), default=Arch.default()._arch, help="Determines the architecture for which to download executables and such.")
    parser.add_argument("-o", "--os", choices=Os.allowed().keys(), default=Os.default()._os, help="Determines the operating system for which to download executables and such.")

    parser.add_argument("-L", "--libbrane-path", default="./libbrane_cli.so", help="The path to the shared Brane CLI library.")
    parser.add_argument("-1", "--brane-api", default=get_default_api_addr(), help="The address of the Brane API service to connect to.")
    parser.add_argument("-2", "--brane-drv", default=get_default_drv_addr(), help="The address of the Brane driver service to connect to.")
    parser.add_argument("-3", "--brane-data-dir", default="./data", help="The notebook directory to map in the IDE container.")
    parser.add_argument("-4", "--brane-certs-dir", default=get_default_certs_dir(), help="The notebook directory to map in the IDE container.")
    parser.add_argument("-5", "--brane-notebook-dir", default="./notebooks", help="The notebook directory to map in the IDE container.")
    parser.add_argument("-D", "--docker", default="docker", help="The `docker`-command to call for any Docker commands.")
    parser.add_argument("-C", "--docker-compose", default="docker compose", help="The `docker compose`-command to call for any Docker Compose commands.")
    parser.add_argument("-S", "--docker-socket", default=("npipe:////./pipe/docker_engine" if Os.default() == Os.windows() else "/var/run/docker.sock"), help="The location of the Docker socket to connect to.")

    # Parse the arguments
    args = parser.parse_args()
    args.arch = Arch(args.arch)
    args.os = Os(args.os)
    args.docker = shlex.split(args.docker)
    args.docker_compose = shlex.split(args.docker_compose)

    # Set the globals
    DEBUG = args.debug
    TARGET_ARGS["debug"] = "1" if DEBUG else "0"
    TARGET_ARGS["libbrane_cli"] = args.libbrane_path
    TARGET_ARGS["brane_api"] = args.brane_api
    TARGET_ARGS["brane_drv"] = args.brane_drv
    TARGET_ARGS["brane_data_dir"] = args.brane_data_dir
    TARGET_ARGS["brane_certs_dir"] = args.brane_certs_dir
    TARGET_ARGS["brane_notebook_dir"] = args.brane_notebook_dir
    TARGET_ARGS["brane_notebook_dir"] = args.brane_notebook_dir
    TARGET_ARGS["docker"] = args.docker
    TARGET_ARGS["docker_compose"] = args.docker_compose
    TARGET_ARGS["docker_socket"] = args.docker_socket

    # Run the code to execute
    if not args.targets:
        exit(main(args.TARGETS, args.arch, args.os, args.force, args.dry_run))
    else:
        exit(list_targets())
