import os

class LaunchProtocol:
    def __init__(self, msg: dict):
        assert msg['arguments']['type'] == 'asy'
        self.arguments = msg['arguments']

        self.filename = self.arguments['program']

        if 'workingDirectory' in self.arguments:
            self.workingDir = self.arguments['workingDirectory'] + os.sep
        else:
            self.workingDir is None