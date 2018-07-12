#!/usr/bin/env python3

import asydebugger
import sys


def main(args):
    # for initialize request
    debugger = asydebugger.AsymptoteDebugger()
    return debugger.event_loop()


if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
