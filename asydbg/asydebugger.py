import dbgprotocol.base_protocol as bp
import dbgprotocol.launch_protocol as lp

import sys
import subprocess
import os
import queue
import threading

def log(txt: str):
    sys.stderr.write('\r\n')
    sys.stderr.write(txt)
    sys.stderr.write('\r\n')
    sys.stderr.flush()

class BreakCondition:
    breakpoint = 0
    stepin = 1

class AsymptoteDebugger:
    @property
    def capabilites(self) -> dict:
        return {
            'supportsConfigurationDoneRequest': True, 
            'supportsFunctionBreakpoints': False,
            'supportsStepBack': False,
            'supportsCompletionsRequest': False,
            'supportsTerminateThreadsRequest': False
        }

    def __init__(self):
        self._active = True
        self._asyProcess = None
        self._debugMode = True
        self._breakCondition = None
        self._lastBreakInfo = None

        self._fileName = None
        self._workingDir = None
        self.stack_frame_counter = 0

        self.msgqueue = queue.Queue()
        self.outqueue = queue.Queue()

        self._asyReadThread = None
        self._msgFetchThread = threading.Thread(target=self.fetch_vscode_msg)
        self._msgFetchThread.daemon = True
        self._msgFetchThread.start()

        self._outQueueThread = threading.Thread(target=self.send_messages)
        self._outQueueThread.daemon = True
        self._outQueueThread.start()

        self._fin = None
        self._fout = None

    def send_msg(self, msg: bp.DebugProtocol):
        self.outqueue.put(msg)

    def initialize(self, msg):
        response = bp.ResponseProtocol(msg, body=self.capabilites)
        self.send_msg(response)

        initializedEvent = bp.EventProtcol('initialized')
        self.send_msg(initializedEvent)

    def send_messages(self):
        counter = 1
        while self._active:
            msg = self.outqueue.get()
            msg['seq'] = counter
            msg.send()

            log('out')
            log(str(msg._baseObj))
            counter += 1
            

    def disconnect(self, msg):
        assert msg['command'] == 'disconnect'
        self.send_msg(bp.ResponseProtocol(msg))

        if ('terminateDebuggee', True) in msg.items():
                self._active = False
        elif ('terminateDebuggee', False) in msg.items():
            pass
        else:
            self._active = False

    def kill_asy(self):
        if self._asyProcess is not None:
            self._asyProcess.kill()
            self._asyProcess.wait()

    def fetch_asy_msg(self):
        while self._active:
            if self._asyProcess is None:
                continue

            msg = bp.read_msg(self._fin)
            log('asy in')
            log(str(msg))
            self.msgqueue.put((msg, bp.ProtocolType.asy))

    def fetch_vscode_msg(self):
        while self._active:
            msg = bp.read_msg()
            log('in:')
            log(str(msg))
            self.msgqueue.put((msg,  bp.ProtocolType.vscode))

    def launch(self, msg):
        assert msg['command'] == 'launch'

        asyArgs = ['asy', '-noV']

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


        launchArgs = lp.LaunchProtocol(msg)
        
        self._fileName = launchArgs.filename
        self._workingDir = launchArgs.workingDir

        if self._workingDir is not None:
            asyArgs += ['-o', self._workingDir]

        self._asyProcess = subprocess.Popen(args=asyArgs, close_fds=False, 
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        self._asyReadThread = threading.Thread(target=self.fetch_asy_msg)
        self._asyReadThread.daemon = True
        self._asyReadThread.start()

        # launch

        self._fout.write('enableDbgAdapter();\n')
        self._fout.write('stop("{0}", 1);\n'.format(self._fileName))
        self._fout.write('import "{0}" as __entry__;\n'.format(self._fileName))
        self._fout.flush()

        self.send_msg(bp.ResponseProtocol(msg))

    def report_threads(self, msg):
        thread_list = [{
                'id': threading.main_thread().ident,
                'name': threading.main_thread().name
            }
            ]

        thread_body = { 'threads': thread_list }
        self.send_msg(bp.ResponseProtocol(msg, body=thread_body))

    def send_break(self, asymsg:dict):
        newevent = bp.EventProtcol('stopped')
        newevent['body'] = {
            'reason': 'breakpoint',
            'threadId': threading.main_thread().ident
        }

        self._lastBreakInfo = asymsg
        self.send_msg(newevent)

    def report_stack_trace(self, msg):
        
        response = bp.ResponseProtocol(msg)
        filename = self._lastBreakInfo['file']
        response['body'] = {
            'stackFrames': [
                {
                    'id': self.stack_frame_counter,
                    'name': 'asyframe',
                    'source': {
                        'name': os.path.basename(filename),
                        'path': filename
                    }, 
                    'line': self._lastBreakInfo['line'],
                    'column': self._lastBreakInfo['col']
                }
            ]
        }

        self.stack_frame_counter += 1
        self.send_msg(response)

    def event_loop(self):
        while self._active:
            msg, msg_src = self.msgqueue.get()
            if msg_src == bp.ProtocolType.vscode:
                # requests
                if msg['type'] == 'request':
                    if msg['command'] == 'initialize':
                        self.initialize(msg)
                    elif msg['command'] == 'disconnect':
                        self.disconnect(msg)
                    elif msg['command'] == 'launch':
                        self.launch(msg)
                    elif msg['command'] == 'threads':
                        self.report_threads(msg)
                    elif msg['command'] == 'stackTrace':
                        self.report_stack_trace(msg)

            else:
                if msg['type'] == 'break':
                    self.send_break(msg)
                    

        self._msgFetchThread.join()
        self._outQueueThread.join()

        if self._asyReadThread is not None:
            self._asyReadThread.join()

        self.kill_asy()


