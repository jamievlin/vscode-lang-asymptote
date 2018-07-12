import dbgprotocol

import sys
import subprocess

def log(txt: str):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    sys.stderr.flush()



class AsymptoteDebugger:
    def __init__(self):
        self._active = False
        self._asyProcess = None

    def initialize(self):
        response = dbgprotocol.ResponseProtocol(1, True, '')
        response.send()

        initializedEvent = dbgprotocol.EventProtcol(2, 'initialized')
        initializedEvent.send()

    def disconnect(self, msg):
        assert msg['command'] == 'disconnect'
        response = dbgprotocol.ResponseProtocol(1, True, '')
        response.send()

        if 'terminateDebuggee' in msg:
            if msg['terminateDebuggee']:
                self._active = False
        else:
            self._active = False

    def launch(self, msg):
        assert msg['command'] == 'launch'
        raise Exception(str(msg))

    def event_loop(self):
        self._active = True
        while self._active:
            msg = dbgprotocol.read_msg()

            if msg['command'] == 'initialize':
                self.initialize()

            if msg['command'] == 'disconnect':
                self.disconnect(msg)

            if msg['command'] == 'launch':
                self.launch(msg)

