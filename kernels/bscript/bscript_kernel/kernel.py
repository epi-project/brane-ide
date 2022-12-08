# KERNEL.py
#   by Lut99
#
# Created:
#   02 May 2022, 17:34:40
# Last edited:
#   08 Dec 2022, 17:09:13
# Auto updated?
#   Yes
#
# Description:
#   Custom JupyterLab kernel for BraneScript.
#


import sys
import json
import os
import pty
import select
import typing

from base64 import b64encode
from filetype import image_match
from grpc import insecure_channel, RpcError
from ipykernel.kernelbase import Kernel
from os import getenv, path

from .driver_pb2 import CreateSessionRequest, ExecuteRequest
from .driver_pb2_grpc import DriverServiceStub





##### GLOBAL "CONSTANTS" #####
# Determines the address of the remote Brane instance's API
BRANE_API_URL  = getenv('BRANE_API_URL', 'brane-api:50051')
# Determines the address of the remote Brane instance's driver
BRANE_DRV_URL  = getenv('BRANE_DRV_URL', 'brane-drv:50053')

# Determines the container-local path of the data directory
BRANE_DATA_DIR = getenv('BRANE_DATA_DIR', '/home/jovyan/data')





##### HELPER FUNCTIONS #####
def poll_pid(pid: int) -> bool:
    """
    Returns if the process with the given PID is alive.

    Code from: https://stackoverflow.com/a/568285
    """

    # Sending signal 0 apparently doesn't do anything, but does error if the PID doesn't exist anymore
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True





##### KERNEL CLASS #####
class BraneScriptKernel(Kernel):
    implementation = 'BraneScript'
    implementation_version = '2.0.0'
    banner = 'bscript'
    language = 'no-op'
    language_version = '0.5.0'
    language_info = {
        'name': 'BraneScript',
        'mimetype': 'text/plain',
        'file_extension': '.bk',
    }

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)

        self.driver = DriverServiceStub(insecure_channel(BRANE_DRV_URL))
        self.session_uuid = None

        # Also initialize a running `branec` process in streaming mode
        print("Spinning up new `branec` executable")
        # self.handle = pty.Popen(["/branec", "--language", "bscript", "--stream", "--compact", "--data", f"Remote<{BRANE_API_URL}>"], stdin=ptyprocess.PIPE, stdout=ptyprocess.PIPE, stderr=ptyprocess.PIPE, bufsize=1, universal_newlines=True, env={
        #     "PATH": os.environ["PATH"],
        # })
        # TODO: This pty business is horrible, so I think we should just edit `branec` to take in something else then EOF...
        (self.branec_pid, self.branec_fd) = pty.fork(["/branec", "--language", "bscript", "--stream", "--compact", "--data", f"Remote<{BRANE_API_URL}>"])

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        # Preprocess the code by quitting if empty and otherwise processing magic statements
        if not code.strip():
            return self.complete()
        code = self.intercept_magic(code)

        # Compile the code first
        res = self.compile(code)
        if res is None:
            # An error has already been provided to the user
            return self.complete()
        (code, warnings) = res

        # Handle any errors
        self.send_status_json({
            "done": False,
            "stdout": f"Compiled code: \"{code}\"",
            "stderr": "",
            "debug": "",
            "value": None,
        })
        if len(warnings) > 0:
            self.send_status_json({
                "done": False,
                "stdout": "",
                "stderr": f"{warnings}",
                "debug": "",
                "value": None,
            })

        # If we have no session attached yet, attach one
        if self.session_uuid is None:
            session = self.driver.CreateSession(CreateSessionRequest())
            self.session_uuid = session.uuid

        # Try to send the code to the driver using gRPC
        try:
            # Send the command and skip the first reply(?)
            stream = self.driver.Execute(ExecuteRequest(uuid=self.session_uuid, input=code))
            stream.next

            # For all other replies, publish the reply in appropriate ways
            for reply in stream:
                # Convert the reply to the appropriate JSON format
                status = self.create_status_json(reply)

                # If the status' stdout happens to point to a file, return that instead
                try:
                    file = self.try_as_file_output(status["stdout"])
                except Exception as e:
                    # The command failed: show the user why
                    self.send_status_json({
                        "done": status["done"],
                        "stdout": "",
                        "stderr": f"{e}",
                        "debug": "",
                        "value": None,
                    })
                    continue
                if file is not None:
                    # Send the file directly instead
                    self.send_response(self.iopub_socket, 'display_data', file)
                    continue

                # Publish the status update
                self.send_status_json(status)

        except KeyboardInterrupt:
            # Make sure we can interrupt the process
            return {'status': 'abort', 'execution_count': self.execution_count}
        except RpcError as e:
            # We could not get the stream back: show the error
            self.send_status_json({
                "done": True,
                "stdout": "",
                "stderr": e.details(),
                "debug": "",
                "value": None,
            })

        # Done
        return self.complete()

    def create_status_json(self, reply):
        return {
            "done": reply.close,
            "stdout": reply.stdout if reply.stdout is not None else "",
            "stderr": reply.stderr if reply.stderr is not None else "",
            "debug": reply.debug if reply.debug is not None else "",
        }

    def send_status_json(self, status):
        """
            Sends a status JSON to the renderer to be rendered.
        """

        # If it has a stdout part, send it as a stream
        if status["stdout"] is not None and len(status["stdout"]) > 0:
            self.send_response(self.iopub_socket, 'stream', {
                'name': 'stdout',
                'text': f'{status["stdout"]}\n'
            })

        # If it has a stderr part, send it as a stream
        if status["stderr"] is not None and len(status["stderr"]) > 0:
            self.send_response(self.iopub_socket, 'stream', {
                'name': 'stderr',
                'text': f'{status["stderr"]}\n'
            })

        # If it's a debug message, then send it as one
        if status["debug"] is not None and len(status["debug"]) > 0:
            print(f'Remote: {status["debug"]}')
            sys.stdout.flush()

        # If it's a value, show that
        if status["value"] is not None and len(status["value"]) > 0:
            self.send_response(self.iopub_socket, 'stream', {
                'name': 'stdout',
                'text': f'Workflow returned result: {status["value"]}',
            })


    def complete(self):
        """
        This marks the current cell as complete
        """
        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }


    def intercept_magic(self, code):
        """
        Checks for magic and invokes it. This is done before any BraneScript code.
        No need to filter magic out, as it is considered a comment by BraneScript.
        But we will anyway to save traffic
        """
        magics = {
            'attach': self.attach,
            'session': lambda: self.send_status_json({
                "done": True,
                "stdout": self.session_uuid,
                "stderr": "",
                "debug": ""
            }),
        }

        result = ""
        for line in code.split("\n"):
            if line.startswith("//!"):
                # This is a magic command
                command = line[3:].strip().split(' ')
                magic = magics.get(command[0])

                if magic is not None:
                    magic(*command[1:])
            else:
                # Add the line to the dict
                result += line + "\n"

        # Return the code minus the stripped magic lines
        return result

    def compile(self, code: str) -> typing.Optional[tuple[str, str]]:
        """
        Compiles the given code using the `branec` tool.
        Returns a JSON string that represents the compiled workflow.

        # Arguments
        - `code`: The source code to compile.
        """

        # Assert it didn't die too early
        if not poll_pid(self.branec_pid):
            err = f"`branec` process terminated with exit code {os.waitpid(self.branec_pid, 0)[1]}"
            if len(select.select([ self.branec_fd ], [], [], 0)[0]) > 0:
                err += f": {os.read(self.branec_fd, 4000000)}"
            raise RuntimeError(err)

        # Feed the code to the compiler
        codeline = code.replace('\n', '\\n')
        self.send_status_json({"done": False, "stdout": f"Sending '{codeline}' to branec", "stderr": "", "debug": "", "value": None})
        self.handle.stdin.write(f"{code}\n")

        # Read its result until we see '---END---'
        self.send_status_json({"done": False, "stdout": "Reading compiler reply", "stderr": "", "debug": "", "value": None})
        stdout = ""
        stderr = ""
        while True:
            # Block until either of the streams reports something available
            self.send_status_json({"done": False, "stdout": "Waiting for reply to become available...", "stderr": "", "debug": "", "value": None})
            readable, _, _ = select.select([ self.handle.stdout.fileno(), self.handle.stderr.fileno() ], {}, {}, 30)
            if len(readable) == 0:
                raise RuntimeError("`branec` took longer than 30 seconds to come up with a reply")

            # Read both the stdout and stderr lines
            stop  = False
            error = False
            if self.handle.stdout.fileno() in readable:
                # Read as many lines as we can
                while len(select.select([ self.handle.stdout.fileno() ], [], [], 0))[0] > 0:
                    line = self.handle.stdout.readline().strip()
                    stdout += line
                    # If the line indicates a stop, do so
                    lineline = line.replace("\n", "\\n")
                    self.send_status_json({"done": False, "stdout": f"> {lineline}", "stderr": "", "debug": "", "value": None})
                    if line == "---END---" or line == "---ERROR---":
                        stop = True
                    if line == "---ERROR---":
                        error = True
            if self.handle.stderr.fileno() in readable:
                # Read as many lines as we can
                while len(select.select([ self.handle.stderr.fileno() ], [], [], 0))[0] > 0:
                    stderr += self.handle.stderr.readline().strip()

            # Stop if necessary
            if stop:
                if error:
                    self.send_status_json({"done": False, "stdout": "", "stderr": stderr, "debug": "", "value": None})
                    return None
                break

        # If there is any warning, return that
        warnings = ""
        # if len(select.select([ self.handle.stderr.fileno() ], [], [], 0)[0]) > 0:
        #     warnings += self.handle.stderr.read()

        # Return the parsed thing
        return (stdout, warnings)


    def attach(self, session_uuid):
        """
        Attach to an existing session. Variables will be restored, imports not.
        """
        self.session_uuid = session_uuid


    def try_as_file_output(self, output: str):
        """
            Tries to read the given stdout text as a file in the /data directory.

            Returns 'None' if it fails, or the file contents (ready for sending with self.send_response()).
        """

        # Make sure it starts with a file pointing to the data directory
        if not output.startswith("file:///data"):
            if output.startswith("file://"):
                raise RuntimeError(f"File '{output}' does not live in data directory: cannot show.")
            return None

        # Replace the data directory with the home folder and make sure it exists
        output = BRANE_DATA_DIR + output[12:]
        if not path.isfile(output):
            raise RuntimeError(f"File '{output}' does not exist.")

        # It does; try to get the extension and (possible) image metadata of the file
        try:
            extension = path.splitext(output)[1].lower()
            kind = image_match(output)
        except Exception:
            raise RuntimeError(f"Could not get extension from '{output}': cannot determine file type.")

        # Switch to render as various file types
        if extension == '.json':
            # Read the JSON data (any errors should be caught by a parent try/except)
            with open (output, 'rb') as f:
                json_data = json.loads(f.read())

            # Return the JSON struct with the data
            return {
                'data': {
                    'application/json': json_data
                },
                'metadata': {}
            }

        elif extension == '.html':
            # Read the HTML data (any errors should be caught by a parent try/except)
            with open (output, 'r') as f:
                html_data = f.read()

            # Return the data as HTML
            return {
                'data': {
                    'text/html': html_data
                },
                'metadata': {}
            }

        elif kind is not None:
            # It's an image, so load the binary data as Base64 encoded
            with open (output, 'rb') as f:
                image_data = b64encode(f.read()).decode('ascii')

            # Return it with the appropriate mime type
            return {
                'data': {
                    kind.mime: image_data
                },
                'metadata': {}
            }

        # Unknown extension
        else:
            # Read as raw text
            with open (output, 'r') as f:
                raw_data = f.read()

            # Return it with the appropriate mime type
            return {
                'data': {
                    "text/plain": raw_data
                },
                'metadata': {}
            }
