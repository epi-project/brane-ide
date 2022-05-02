# TEST.py
#   by Lut99
#
# Created:
#   28 Apr 2022, 11:42:21
# Last edited:
#   28 Apr 2022, 12:21:41
# Auto updated?
#   Yes
#
# Description:
#   Simple test file for me to run the kernel locally without JupyterLab in
#   the way.
#

from base64 import b64encode
from filetype import image_match
from json import loads
from os import path
from pprint import pprint

from grpc import insecure_channel, RpcError

from driver_pb2 import CreateSessionRequest, ExecuteRequest
from driver_pb2_grpc import DriverServiceStub


##### HELPER FUNCTIONS #####
def intercept_magic(code):
    """
    Checks for magic and invokes it. This is done before any BraneScript code.
    No need to filter magic out, as it is considered a comment by BraneScript.
    """
    return



def create_status_json(reply):
    pprint(vars(reply))
    return {
        "done": reply.close,
        "output": reply.output,
        "bytecode": reply.bytecode,
    }



def publish_status(status, update):
    """
    Publishes a status payload on Jupyter's IOPub channel.
    Subsequent calls should be updates, to support delta rendering.
    """
    content = {
        'data': {
            'application/vnd.brane.invocation+json': status
        },
        'metadata': {},
        'transient': {}
    }

    message_type = "update_display_data" if update else "display_data"
    send_response(message_type, content)



def publish_stream(stream, text):
    """
    Publishes a 'stream' message on the Jupyter IOPub channel.
    """
    content = {
        'name' : stream,
        'text' : text,
    }

    send_response('stream', content)



def send_response(message_type, content):
    print("Result:")
    print(f" - Type: {message_type}")
    print(f" - Content: {content}")



def try_as_file_output(output: str):
    """

    """
    if not output.startswith("\"/data/"):
        return None

    output = output.strip('"').replace("/data", "/home/lut_99/UvA/EPI/brane-ide/data")
    if not path.isfile(output):
        return None

    extension = path.splitext(output)[1]

    # Render as JSON, if file extension is .json
    if extension == '.json':
        try:
            with open (output, 'rb') as f:
                json_data = loads(f.read())
        except:
            json_data = {
                'message': 'Please check the file, it doesn\'t seems to be valid JSON.'
            }

        return {
            'data': {
                'application/json': json_data
            },
            'metadata': {}
        }

    # Render as HTML, if file extension is .html
    extension = path.splitext(output)[1]
    if extension == '.html':
        with open (output, 'r') as f:
            html_data = f.read()

        return {
            'data': {
                'text/html': html_data
            },
            'metadata': {}
        }

    kind = image_match(output)
    if kind is not None:
        with open (output, 'rb') as f:
            image_data = b64encode(f.read()).decode('ascii')

        return {
            'data': {
                kind.mime: image_data
            },
            'metadata': {}
        }





##### ENTRYPOINT #####
if __name__ == "__main__":
    code = "print(\"test\");"
    current_bytecode = None
    driver = DriverServiceStub(insecure_channel("127.0.0.1:50053"))

    if not code.strip():
        print("Return: Complete")
        exit(0)

    intercept_magic(code)

    # Create session, if not already exists
    session = driver.CreateSession(CreateSessionRequest())
    session_uuid = session.uuid

    interrupted = False
    try:
        stream = driver.Execute(ExecuteRequest(uuid=session_uuid, input=code))
        stream.next

        for reply in stream:
            print("Reply:")
            print(f" - Close: {reply.close}")
            print(" - Stdout: {}".format(reply.stdout.replace('\n', '\\n')))
            print(" - Stderr: {}".format(reply.stderr.replace('\n', '\\n')))
            print(" - Debug: {}".format(reply.debug.replace('\n', '\\n')))
            continue
            status = create_status_json(reply)
            publish_status(status, not reply.close)

            if reply.close:
                file_output = try_as_file_output(reply.output)
                send_response("display_data", file_output)

    except KeyboardInterrupt:
        # TODO: support keyboard interrupt (like CLI REPL)
        interrupted = True
    except RpcError as e:
        publish_stream("stderr", e.details())

    if interrupted:
        print("Return: Abort")
        exit(0)
    else:
        print("Return: Complete")
        exit(0)
