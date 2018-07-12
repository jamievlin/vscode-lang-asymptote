import dbgprotocol.base_protocol as bp
import dbgprotocol.launch_protocol as lp

import sys
import subprocess
import os


def log(txt: str):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    sys.stderr.flush()


class AsymptoteDebugger:
    def __init__(self):
        self._active = False
        self._asyProcess = None
        self._debugMode = True

        self._fileName = None
        self._workingDir = None

        self._fin = None
        self._fout = None

    def initialize(self):
        response = bp.ResponseProtocol(1, True, '')
        response.send()

        initializedEvent = bp.EventProtcol(2, 'initialized')
        initializedEvent.send()

    def disconnect(self, msg):
        assert msg['command'] == 'disconnect'
        response = bp.ResponseProtocol(1, True, '')
        response.send()

        if ('terminateDebuggee', True) in msg.items():
                self._active = False
        elif ('terminateDebuggee', False) in msg.items():
            pass
        else:
            self._active = False

    def kill_asy(self):
        return 
        if self._asyProcess is not None:
            self._asyProcess.kill()
            self._asyProcess.wait()

    def launch(self, msg):
        assert msg['command'] == 'launch'

        asyArgs = ['asy']
        if ('noDebug', True) not in msg['arguments'].items():
            self._debugMode = False

        if os.name != 'nt':
            rx, wx = os.pipe()
            ra, wa = os.pipe()

            os.set_inheritable(rx, True)
            os.set_inheritable(wx, True)
            os.set_inheritable(ra, True)
            os.set_inheritable(wa, True)

            asyArgs += ['-inpipe={0:d}'.format(rx), '-outpipe={0:d}'.format(wa)]

            self._fin = os.fdopen(ra, 'r')
            self._fout = os.fdopen(wx, 'w')

        else:
            raise NotImplementedError

        launchArgs = lp.LaunchProtocol(msg)
        
        self._fileName = launchArgs.filename
        self._workingDir = launchArgs.workingDir

        if self._workingDir is not None:
            asyArgs += ['-o', self._workingDir]
        self._asyProcess = subprocess.Popen(args=asyArgs, close_fds=False)
        
        # launch
        self._fout.write('import "{0}" as __entry__;\n'.format(self._fileName))
        self._fout.flush()

        log(self._fileName)

    def event_loop(self):
        self._active = True
        while self._active:
            msg = bp.read_msg()

            if msg['command'] == 'initialize':
                self.initialize()

            if msg['command'] == 'disconnect':
                self.disconnect(msg)

            if msg['command'] == 'launch':
                self.launch(msg)
        self.kill_asy()

