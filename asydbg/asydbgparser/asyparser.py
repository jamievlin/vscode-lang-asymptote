import typing as ty
import re


class AsymptotePauseMsg:
    @classmethod
    def parseAsyLine(cls, line:str):
        # see 
        matchStr = r'^(.+): (\d+\.\d+)\? \[.*\] $'
        matchResult = re.match(matchStr, line)
        if matchResult is None:
            return None
        else:
            filename = matchResult.group(1)
            line, col = [int(val) for val in matchResult.group(2).split('.')]
            return AsymptotePauseMsg(filename, (line, col))

    def __init__(self, file: str, line: ty.Tuple[int,int]):
        self._file_name = file
        self._line, self._col = line

    @property
    def file_name(self):
        return self._file_name

    @property
    def line(self):
        return self._line

    @property
    def col(self):
        return self._col
    
