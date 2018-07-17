import dbgprotocol.base_protocol as bp
import dbgprotocol.launch_protocol as lp

import asydbgparser.data_formats as df

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
        self._breakpoints = {}

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
        launchArgs = lp.LaunchProtocol(msg)

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
        # self._fout.write('stop("{0}", 1);\n'.format(self._fileName))
        self.send_msg(bp.ResponseProtocol(msg))

    def handle_breakpoints(self, msg):
        assert msg.event == 'breakpoint'

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

    def set_breakpoints(self, msg):
        breakpoints_args = df.JSInterface(msg['arguments'])
        filename = breakpoints_args.source.path

        self._breakpoints[filename] = breakpoints_args.breakpoints

        for filename in self._breakpoints:
            for bp_ in self._breakpoints[filename]:
                breakpoint_txt = 'stop("{0}", {1:d});'.format(
                    filename, bp_['line'])
                self._fout.write(breakpoint_txt + '\n')
                log(breakpoint_txt)

        response = bp.ResponseProtocol(msg, body={
            'breakpoints': [
                {'verified': False} 
            ] * len(self._breakpoints[filename])
        })

        self.send_msg(response)

    def report_stack_trace(self, msg):
        
        response = bp.ResponseProtocol(msg)
        filename = self._lastBreakInfo['file']

        # NOTE: Until a proper stackframe is implemented, will remain incomplete. 
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

    def finish_config(self, msg):
        self._fout.write('import "{0}" as __entry__;\n'.format(self._fileName))
        self._fout.flush()

        self.send_msg(bp.ResponseProtocol(msg))

    def event_loop(self):
        while self._active:
            msg, msg_src = self.msgqueue.get()
            if msg_src == bp.ProtocolType.vscode:
                if msg['type'] == 'request':
                    cmd = msg['command']
                    if cmd == 'initialize':
                        self.initialize(msg)
                    elif cmd == 'disconnect':
                        self.disconnect(msg)
                    elif cmd == 'launch':
                        self.launch(msg)
                    elif cmd == 'threads':
                        self.report_threads(msg)
                    elif cmd == 'stackTrace':
                        self.report_stack_trace(msg)
                    elif cmd == 'setBreakpoints':
                        self.set_breakpoints(msg)
                    elif cmd == 'configurationDone':
                        self.finish_config(msg)

                elif msg.type == 'event':
                    if msg.event == 'breakpoint':
                        self.handle_breakpoints(msg)

            else:
                if msg['type'] == 'break':
                    self.send_break(msg)
                    

        self._msgFetchThread.join()
        self._outQueueThread.join()

        if self._asyReadThread is not None:
            self._asyReadThread.join()

        self.kill_asy()


