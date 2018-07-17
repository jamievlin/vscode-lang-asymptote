import os

class JSInterface:
    def __init__(self, msg: dict):
        self._baseInfo = {}
        for key, value in msg.items():
            if isinstance(value, dict):
                self._baseInfo[key] = JSInterface(value)
            else:
                self._baseInfo[key] = value

    def __getitem__(self ,key):
        return self._baseInfo[key]

    def __setitem__(self, key, value):
        self._baseInfo[key] = value

    def __getattr__(self, key):
        return self._baseInfo[key]

    def getdict(self) -> dict:
        newDict = {}
        for key, val in self._baseInfo.items():
            if isinstance(val, JSInterface):
                newDict[key] = val.getdict()
            else:
                newDict[key] = val
        return newDict

class Source(JSInterface):
    def __init__(self, path: str, name: str=None):
        super().__init__()

        if name is None:
            name = os.path.basename(path)

        self['path'] = path
        self['name'] = name

class Breakpoint(JSInterface):
    def __init__(self, src: Source, line: int, col: int):
        super().__init__()

        self['source'] = src
        self['line'] = line
        self['col'] = col

