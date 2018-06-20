

import sys
import io

def main(args):
    sys.stderr.write(sys.stdin.readline())


if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
