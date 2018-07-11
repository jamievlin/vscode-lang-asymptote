
#!/usr/bin/env python3

import sys
import io
import json

def read_msg() -> dict:
    header = sys.stdin.readline()
    assert header.startswith('Content-Length: ')
    bytenum = int(header.replace('Content-Length: ', '', 1))
    sys.stdin.readline()

    msg = sys.stdin.read(bytenum)
    return json.loads(msg)

def log(txt: str):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    # sys.stderr.flush()

def main(args):
    msg = read_msg()
    log(str(msg))


if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
