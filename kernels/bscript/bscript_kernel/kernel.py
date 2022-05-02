# KERNEL.py
#   by Lut99
#
# Created:
#   02 May 2022, 17:34:40
# Last edited:
#   02 May 2022, 18:29:37
# Auto updated?
#   Yes
#
# Description:
#   Custom JupyterLab kernel for BraneScript.
#


import sys
import json

from base64 import b64encode
from filetype import image_match
from grpc import insecure_channel, RpcError
from ipykernel.kernelbase import Kernel
from os import getenv, path

from .driver_pb2 import CreateSessionRequest, ExecuteRequest
from .driver_pb2_grpc import DriverServiceStub





##### GLOBAL "CONSTANTS" #####
# Determines the address of the remote Brane instance
BRANE_DRV_URL  = getenv('BRANE_DRV_URL', 'brane-drv:50053')

# Determines the container-local path of the data directory
BRANE_DATA_DIR = getenv('BRANE_DATA_DIR', '/home/jovyan/data')





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

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        # Preprocess the code by quitting if empty and otherwise processing magic statements
        if not code.strip():
            return self.complete()
        code = self.intercept_magic(code)

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
                        "debug": ""
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
                "debug": ""
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
