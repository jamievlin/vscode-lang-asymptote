import json
import sys
import typing as ty

def read_msg(fin=sys.stdin) -> dict:
    header = fin.readline()
    assert header.startswith('Content-Length: ')
    bytenum = int(header.replace('Content-Length: ', '', 1))
    fin.readline()

    msg = fin.read(bytenum)
    return json.loads(msg)

class ProtocolType:
    asy = 0
    vscode = 1


class DebugProtocol:
    def __init__(self, type_:str):
        self._baseObj = {
            'seq': -1, 
            'type': type_
        }

    def set_seq(self, seq:int):
        self['seq'] = seq

    def create_msg(self) -> str:
        new_obj_txt = json.dumps(self._baseObj)

        return 'Content-Length: {0:d}\r\n\r\n{1}'.format(len(new_obj_txt), new_obj_txt)

    def __getitem__(self, key):
        return self._baseObj[key]

    def __setitem__(self, key, value):
        self._baseObj[key] = value

    def __getattr__(self, attr):
        return self._baseObj[attr]

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
        self['event'] = event

        if body is not None:
            self['body'] = body

class ResponseProtocol(DebugProtocol):
    def __init__(self, original_request: ty.Union[RequestProtcol, dict]=None, success: bool=True,
        message:str=None, body=None):

        super().__init__(type_='response')
        self._baseObj.update({
            "request_seq": -1,
            "success": success,
            "command": ''
            })

        if original_request is not None:
            self['command'] = original_request['command']
            self['request_seq'] = original_request['seq']

        if message is not None:
            self['message'] = message

        if body is not None:
            self['body'] = body
        

