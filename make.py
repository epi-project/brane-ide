#!/usr/bin/env python3
# MAKE.py
#   by Lut99
#
# Created:
#   02 Aug 2023, 08:38:41
# Last edited:
#   09 Aug 2023, 09:55:17
# Auto updated?
#   Yes
#
# Description:
#   Make script for the Brane IDE project.
#

import abc
import argparse
import os
import platform
import shlex
import subprocess
import sys
import typing
from typing_extensions import Self


##### GLOBALS #####
# Determines if `pdebug()` does anything
DEBUG: bool = False

# Determines any arguments relevant only for targets
TARGET_ARGS: typing.Dict[str, typing.Optional[typing.Any]] = {
    "libbrane_cli": None,
    "brane_api": None,
    "brane_drv": None,
    "brane_notebook_dir": None,
    "docker": None,
    "docker_compose": None,
    "docker_socket": None,
}





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





##### HELPER STRUCTS #####
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

    def __eq__(self, other: Self) -> bool:
        return self._arch == other._arch
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

    def __eq__(self, other: Self) -> bool:
        return self._os == other._os
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
        else:
            self.exe  = exe[0]
            self.args = exe[1:]
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





##### TARGET DEFINITIONS #####
class ShellTarget(Target):
    """
        Just runs a few commands.
    """

    _cmds : typing.List[typing.List[str]]


    def __init__(self, id: str, commands: typing.List[typing.List[str]], deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the ShellTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `commands`: A list of commands (each of which is a list of arguments) to run.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new ShellTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Set the commands
        self._cmds = commands

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

        # Launch processes for each of them
        for cmd in self._cmds:
            # Resolve any commands
            cmd = [ (TARGET_ARGS[c[1:]] if len(c) > 0 and c[0] == "$" else c) for c in cmd ]

            # Run it with the resolved arguments
            (code, _, _) = Process(cmd).execute(dry_run)
            if code != 0:
                raise RuntimeError(f"Failed to run command '{Process.shellify(cmd)}'")

        # Done
        return True

    def is_outdated(self) -> bool:
        """
            Compute whether this target needs to be updated.

            Note that dependencies marking themselves as outdated are already taken care of.

            # Returns
            True if it should be updated, False if it shouldn't.
        """

        # Shell targets are always outdated
        pdebug(f"Marking target '{self.id}' as outdated because shell targets are always outdated")
        return True

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
        args = TARGET_ARGS["docker"] + [ "build", "--load", "-t", self._image ]
        if self._target is not None:
            args += [ "--target", self._target ]
        for arg in self._args:
            args += [ "--build-arg", f"{arg}={self._args[arg]}" ]
        if arch != Arch.default() or os_ != Os.default():
            args += [ "--platform", f"{os_.docker()}/{arch.docker()}" ]
        args += [ "-f", self._file, "." ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]

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
        pdebug(f"Checking if an image named '{self._image}' exists...")
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        (code, stdout, _) = Process(TARGET_ARGS['docker'] + [ "image", "list" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if image '{self._image}' is running")

        # We are only outdated if it does not exist
        if self._image in stdout:
            pdebug(f"Marking target '{self.id}' as up-to-date because image '{self._image}' already exists")
            return False
        else:
            pdebug(f"Marking target '{self.id}' as outdated because no image '{self._image}' is found")
            return True

class RunContainerTarget(Target):
    """
        Starts a Docker container.
    """

    _name       : str
    _image      : str
    _args       : typing.List[str]
    _entrypoint : str
    _commands   : str
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
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        (code, stdout, _) = Process(TARGET_ARGS['docker'] + [ "ps", "-a" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' is running")

        # Remove the container if it exists
        if self._name in stdout:
            pdebug(f"Removing existing container '{self._name}'...")
            (code, _, _) = Process(TARGET_ARGS["docker"] + [ "rm", "-f", self._name ], capture_stdout=True).execute(dry_run)
            if code != 0: raise RuntimeError(f"Failed to run command to remove container '{self._name}'")

        # Construct the Docker arguments
        args = TARGET_ARGS["docker"] + [ "run", "-d", "--name", self._name ]
        for host, cont in self._volumes:
            args += [ "-v", f"{host}:{cont}" ]
        if self._entrypoint is not None:
            args += [ "--entrypoint", self._entrypoint ]
        if self._commands is not None:
            args += [ "--cmd", self._commands ]
        args += [ self._image ] + self._args

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]

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
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        (code, stdout, _) = Process(TARGET_ARGS['docker'] + [ "ps" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' is running")

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
    _env       : typing.Dict[str, str]
    _namespace : typing.Optional[str]


    def __init__(self, id: str, file: str, env: typing.Dict[str, str] = dict(os.environ), namespace: typing.Optional[str] = None, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RunComposeTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `file`: The Docker Compose-file to run.
            - `env`: Any additional environment variables to set for the run.
            - `namespace`: Any project/namespace to set for this run. Can be `None` to stick to compose's default.
            - `deps`: A list of target identifier to mark as dependencies of this target.
            - `description`: Some human-readable description of what this target does.

            # Returns
            A new RunComposeTarget instance.
        """

        # Construct the super
        super().__init__(id, deps, description)

        # Construct ourselves
        self._file      = file
        self._env       = env
        self._namespace = namespace

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
        args = TARGET_ARGS["docker_compose"]
        if self._namespace is not None:
            args += [ "-p", self._namespace ]
        args += [ "-f", self._file, "up", "-d" ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        env["DEBUG"] = "0"
        env["BRANE_API_URL"] = TARGET_ARGS["brane_api"]
        env["BRANE_DRV_URL"] = TARGET_ARGS["brane_drv"]
        env["BRANE_NOTEBOOK_DIR"] = TARGET_ARGS["brane_notebook_dir"]

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
        args = TARGET_ARGS["docker"] + [ "rm" ]
        if self._force:
            args += [ "-f" ]
        args += [ self._name ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]

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
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        (code, stdout, _) = Process(TARGET_ARGS['docker'] + [ "ps", "-a" ], env=env, capture_stdout=True).execute(False, show_cmd=False)
        if code != 0: raise RuntimeError(f"Failed to run command to check if container '{self._name}' exists")

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
    _namespace : str


    def __init__(self, id: str, file: str, namespace: typing.Optional[str] = None, deps: typing.List[str] = [], description: str = ""):
        """
            Constructor for the RmComposeTarget.

            # Arguments
            - `id`: The string identifier for this target.
            - `file`: The Docker Compose-file to run.
            - `namespace`: Any project/namespace to set for this run. Can be `None` to stick to compose's default.
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
        args = TARGET_ARGS["docker_compose"]
        if self._namespace is not None:
            args += [ "-p", self._namespace ]
        args += [ "-f", self._file, "down" ]

        # Build the environment
        env = dict(os.environ)
        env["DOCKER_SOCKET"] = TARGET_ARGS["docker_socket"]
        env["DEBUG"] = "0"
        env["BRANE_API_URL"] = TARGET_ARGS["brane_api"]
        env["BRANE_DRV_URL"] = TARGET_ARGS["brane_drv"]
        env["BRANE_NOTEBOOK_DIR"] = TARGET_ARGS["brane_notebook_dir"]

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

        # Never outdated
        pdebug(f"Marking target '{self.id}' as outdated because compose targets are always outdated")
        return True





##### TARGETS #####
TARGETS: typing.Dict[str, Target] = { t.id: t for t in [
    ### IMAGES ###
    ImageTarget("dev-image", "brane-ide-dev", target="dev", description="Builds the development image for the Brane IDE project."),
    ImageTarget("run-image", "brane-ide-server", target="run", description="Builds the runtime image for the Brane IDE project."),

    ### SHELL TARGETS ###
    ShellTarget("prepare-start-ide", [ [ "mkdir", "-p", "$brane_notebook_dir" ] ], description="Prepares starting the IDE by creating the notebook folder."),
    ShellTarget("libbrane_cli", [ [ "mkdir", "-p", ".tmp" ], [ "cp", "-f", "$libbrane_cli", ".tmp/libbrane_cli.so" ] ], description="Copies the `libbrane_cli.so` shared library to a container-accessible location."),

    ### USER TARGETS ###
    RunContainerTarget("start-dev", "brane-ide-dev", "brane-ide-dev", volumes=[(".", "/source")], entrypoint="sleep", args=[ "infinity" ], deps=["dev-image"], description="Launches the development image for the Brane IDE project. You can connect in this with VS Code's Remote Development extension to access all dependencies."),
    RmContainerTarget("stop-dev", "brane-ide-dev", force=True, description="Stops the development image for the Brane IDE project if it is running, and then removes it."),

    RunComposeTarget("start-ide-quiet", "./docker-compose.yml", namespace="brane-ide", deps=["run-image", "prepare-start-ide", "libbrane_cli"], description="Starts the runtime image for the Brane IDE project without querying the token."),
    ShellTarget("start-ide", [ [ "chmod", "+x", "./get_jupyterlab_token.sh" ], [ "bash", "-c", "echo \"JupyterLab launched at:\" && echo \"    $(./get_jupyterlab_token.sh)\" && echo \"\" && echo \"Enter this link in your browser to connect to the server.\"" ] ], deps=["start-ide-quiet"], description="Starts the runtime image for the Brane IDE project without querying the token."),
    RmComposeTarget("stop-ide", "./docker-compose.yml", namespace="brane-ide", description="Stops the runtime image for the Brane IDE project if it is running, and then removes it."),
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
        if dep_changed: pdebug(f"Marking target '{target.id}' as outdated because its dependency '{dep}' was outdated")

        # Update the changed status
        changed = changed or dep_changed

    # Check if the target itself needs updating
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
    for id in TARGETS:
        print(f"{dim} - {end}{green}{id}{end}{dim}:{end} {TARGETS[id].desc}")





# Actual entrypoint
if __name__ == "__main__":
    # Define the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("TARGETS", nargs='*', help="The target(s) to build. See '--targets' for how to obtain a list of valid targets.")

    parser.add_argument("-t", "--targets", action="store_true", help="If given, prints the list of supported targets and then quits.")

    parser.add_argument("--debug", action="store_true", help="If given, prints additional debug information to the output.")
    parser.add_argument("-f", "--force", action="store_true", help="If given, forces rebuild of everything regardless of whether it wants to be rebuild.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="If given, does not run anything but instead just reports what would've been run.")
    parser.add_argument("-a", "--arch", choices=Arch.allowed().keys(), default=Arch.default()._arch, help="Determines the architecture for which to download executables and such.")
    parser.add_argument("-o", "--os", choices=Os.allowed().keys(), default=Os.default()._os, help="Determines the operating system for which to download executables and such.")

    parser.add_argument("-L", "--libbrane-path", default="./libbrane_cli.so", help="The path to the shared Brane CLI library.")
    parser.add_argument("-1", "--brane-api", default="http://localhost:50051", help="The address of the Brane API service to connect to.")
    parser.add_argument("-2", "--brane-drv", default="grpc://localhost:50053", help="The address of the Brane driver service to connect to.")
    parser.add_argument("-3", "--brane-notebook-dir", default="./notebooks", help="The notebook directory to map in the IDE container.")
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
    TARGET_ARGS["libbrane_cli"] = args.libbrane_path
    TARGET_ARGS["brane_api"] = args.brane_api
    TARGET_ARGS["brane_drv"] = args.brane_drv
    TARGET_ARGS["brane_notebook_dir"] = args.brane_notebook_dir
    TARGET_ARGS["docker"] = args.docker
    TARGET_ARGS["docker_compose"] = args.docker_compose
    TARGET_ARGS["docker_socket"] = args.docker_socket

    # Run the code to execute
    if not args.targets:
        exit(main(args.TARGETS, args.arch, args.os, args.force, args.dry_run))
    else:
        exit(list_targets())
