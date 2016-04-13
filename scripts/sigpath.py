#!/usr/bin/env python
"""
Created on May 2, 2013

@author: David I. Urbina
"""

# imports
import sys

import docopt

# constants
__author__ = 'David I. Urbina'
__version__ = 2.0
# exception classes
# interface functions


def _process_cmd_line(argv):
    """
    usage: sigpath.py [-h] -p dump [dump ...] [-n dump] [-v value [value ...]]
                  [-t {string,number}]

    Generates a list of signature paths to the data of interest

    optional arguments:
      -h, --help            show this help message and exit
      -p dump [dump ...]    list of positive memory dumps
      -n dump               negative memory dump

    value scanning:
      -v value [value ...]  memory dumps' corresponding values
      -t {string,number}    possible encodings
    """
    #    Return a 4-tuple: (positive dumps, negative dump, values, type).
    #    "argv" is a list of arguments, or "None" for "sys.argv[1:]".
    #    '''
    #    if argv is None:
    #        argv = sys.argv[1:]
    #
    #    # initializing the parser object
    #    parser = argparse.ArgumentParser(description='Generates a list of \
    #                                    signature paths to the data of interest')
    #    # defining command options
    #    parser.add_argument('-p', required=True, nargs='+', dest='pos_dumps',
    #                        metavar='dump', help='list of positive memory dumps')
    #    parser.add_argument('-n', dest='neg_dump', metavar='dump',
    #                                                help='negative memory dump')
    #    group = parser.add_argument_group('value scanning')
    #    group.add_argument('-v', nargs='+', dest='values', metavar='value',
    #                                    help="memory dumps' corresponding values")
    #    group.add_argument('-t', dest='type', choices=['string', 'number'],
    #                                                    help='possible encodings')
    #    # checking arguments
    #    args = parser.parse_args(argv)
    #    if args.values and not args.type:
    #        parser.error('Value scanning requires encoding')
    #    if args.values and len(args.pos_dumps) != len(args.values):
    #        parser.error('Different number of memory dumps and values')
    #    if len(args.pos_dumps) == 1 and not args.values:
    #        parser.error('Analysis of one memory dump requires a value')

    docopt()

#    return args.pos_dumps, args.neg_dump, args.values, args.type


def main(argv=None):
    pdumps, ndumps, values, vtype = _process_cmd_line(argv)
    # TODO: controlling the chain calls to modules
    return 0


# classes
# internal functions & classes


if __name__ == '__main__':
    sys.exit(main())
