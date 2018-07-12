import json
import sys

def read_msg() -> dict:
    header = sys.stdin.readline()
    assert header.startswith('Content-Length: ')
    bytenum = int(header.replace('Content-Length: ', '', 1))
    sys.stdin.readline()

    msg = sys.stdin.read(bytenum)
    return json.loads(msg)


class DebugProtocol:
    def __init__(self, type_:str):
        self._baseObj = {
            'seq': -1, 
            'type': type_
        }

    def set_seq(self, seq:int):
        self._baseObj['seq'] = seq

    def create_msg(self) -> str:
        new_obj_txt = json.dumps(self._baseObj)

        return 'Content-Length: {0:d}\r\n\r\n{1}'.format(len(new_obj_txt), new_obj_txt)

    def send(self):
        sys.stdout.write(self.create_msg())
        sys.stdout.flush()

class RequestProtcol(DebugProtocol):
    def __init__(self, command:str, argument=None):
        super().__init__(type_='request')
        self._baseObj['command'] = command

        if argument is not None:
            self._baseObj['arguments'] = argument

class EventProtcol(DebugProtocol):
    def __init__(self, event:str, body=None):
        super().__init__(type_='event')
        self._baseObj['event'] = event

        if body is not None:
            self._baseObj['body'] = body

class ResponseProtocol(DebugProtocol):
    def __init__(self, request_seq:int, success:bool, 
                command:str, message:str=None, body=None):
        super().__init__(type_='response')
        self._baseObj.update({
            "request_seq": request_seq,
            "success": success,
            "command": command,
            })

        if message is not None:
            self._baseObj['message'] = message

        if body is not None:
            self._baseObj['body'] = body
        

