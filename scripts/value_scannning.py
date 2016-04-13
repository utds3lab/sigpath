#!/usr/bin/env python
"""
Created on May 2, 2013

@author: David I. Urbina
"""

# imports
import argparse
import sys
# constants
# exception classes
# interface functions


def _process_cmd_line(argv):
    """Returns a n-tuple: (...)
    "argv" is a list of arguments, or "None" for "sys.argv[1:]".
    """
    if argv is None:
        argv = sys.argv[1:]

    # initializing the parser object
    parser = argparse.ArgumentParser(description='')
    # defining command options
    # parser.add_argument()

    # parsing arguments
    args = parser.parse_args(argv)

    # checking arguments
    # if arg...
    return args


def main(argv=None):
    # args = _process_cmd_line(argv)
    pass


# classes
# internal functions & classes


if __name__ == '__main__':
    sys.exit(main())
