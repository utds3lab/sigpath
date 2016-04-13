#!/usr/bin/env python
"""
Created on Jul 5, 2013

Author: David I. Urbina
"""

# imports
from __future__ import print_function
import logging
import sys

from docopt import docopt

import graph_generator
import memorydump


# constants

__version__ = 1.0

# exception classes
# interface classes


# interface functions

def diff_segments(*seg):
    sets = list()
    for i in xrange(len(seg) - 1):
        sets.append(set(_diff_pair_memory_segments(seg[i], seg[i + 1])))
    return set.intersection(*sets)

# internal classes


# internal functions

def _diff_pair_memory_segments(segment1, segment2):
    offsets = list()
    for s1, s2 in zip(segment1.walk_by_byte(), segment2.walk_by_byte()):
        if s1[0] != s2[0]:
            offsets.append(s1[1])
    if segment1.size > segment2.size:
        l, s = segment1, segment2
    else:  # if segment2.size > segment1.size:
        l, s = segment2, segment1
    for i in xrange(l.size, s.size - 1):
        offsets.append(i)
    return offsets


def _process_cmd_line(argv):
    """Segment diffing.

Usage:
    segment_diffing.py [-v] (-a <address> | --full) <dump>... [-n <neg_dump>]
    segment_diffing.py (--help | --version)

Options:
    <dump>         The list of positive memory dumps.
    -n <neg_dump>  The negative memory dump.
    -a <address>   The address of the data structure to diff.
    -f --full      Diff full memory dump's segments.
    -h --help      Shows this message.
    -v --verbose   Shows details.
    --version      Shows the current version.
    """
    # initializing the parser object
    args = docopt(_process_cmd_line.__doc__, argv=argv, version=__version__)

    # checking arguments
    try:
        if args['-a']:
            args['-a'] = int(args['-a'], 0)
    except ValueError:
        print('Error: Invalid address', args['-a'], file=sys.stderr)
        sys.exit(1)

    if args['--verbose']:
        print(args)
    return (args['<dump>'], args['-n'], args['-a'], args['--full'],
            args['--verbose'])


def main(argv=None):
    dumpfiles, neg_filename, address, full, verbose = _process_cmd_line(argv)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug('Loading positive memory dumps...')
    dumps = map(memorydump.load_memory_dump, dumpfiles)

    if not full:
        graphs = map(graph_generator.generate_graph, dumps)
        segs = map(graph_generator.MemoryGraph.seek_node_by_address, graphs,
                   [address] * len(graphs))
        diffing = diff_segments(*segs)
    else:
        pass
    print(diffing)

    return 0


if __name__ == '__main__':
    sys.exit(main())
