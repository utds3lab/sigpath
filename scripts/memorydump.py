#!/usr/bin/env python
'''
Created on May 2, 2013

@author: David I. Urbina
'''

# imports
from __future__ import print_function
import logging
import sys

from docopt import docopt

import segments

# constants

__version__ = 2.0

# exception classes


# interface classes

class MemoryDump(object):
    '''
    Represents a memory dump.
    '''

    def __init__(self, name, modules=None, heaps=None, stacks=None,
                 private_data=None, segments=None, data=None):
        self.name = name
        self.modules = [] if modules is None else modules
        self.stacks = [] if stacks is None else stacks
        self.heaps = [] if heaps is None else heaps
        self.private_data = [] if private_data is None else private_data
        self.segments = [] if segments is None else segments
        self.data = [] if data is None else data
        self.size = len(self.data)

    def __repr__(self):
        return '<md n={} s={}\nmod={}\nhp={}\nst={}\npd={}\nseg={}>'.format(
            self.name, self.size, self.modules, self.heaps,
            self.stacks, self.private_data, self.segments)

    def __str__(self):
        return self.__repr__()


# internal classes

class _SegmentType:
    Segment = 1
    Heap = 2
    Module = 3
    Pdata = 4
    Stack = 5


# interface functions

def load_memory_dump(dumpfile):
    # Reading metadata files
    data = _read_memory_dump_data(dumpfile + '.core')
    logging.debug('{}.core loaded {} bytes'.format(dumpfile, len(data)))
    mseg = _read_metadata(_SegmentType.Segment, dumpfile + '.segments')
    logging.debug('{}.segments loaded'.format(dumpfile))
    mmod = _read_metadata(_SegmentType.Module, dumpfile + '.modules')
    logging.debug('{}.modules loaded'.format(dumpfile))
    #     mstk = []
    mstk = _read_metadata(_SegmentType.Stack, dumpfile + '.stacks')
    logging.debug('{}.stacks loaded'.format(dumpfile))
    mhp = _read_metadata(_SegmentType.Heap, dumpfile + '.heaps')
    logging.debug('{}.heaps loaded'.format(dumpfile))
    mpd = _read_metadata(_SegmentType.Pdata, dumpfile + '.pdata')
    logging.debug('{}.pdata loaded'.format(dumpfile))
    #     mpd = []
    # Creating MemoryDump object
    seg = [segments.Segment(a, s) for (a, s) in mseg]
    for s in seg:
        s.offset = _ofa(seg, a)
        s.data = data[s.offset:s.offset + s.size]

    mod = list()

    for (a, s, n) in mmod:
        o = _ofa(seg, a)
        mod.append(segments.Module(n, a, s, o, data[o:o + s]))

    hp = list()
    for (a, s) in mhp:
        o = _ofa(seg, a)
        hp.append(segments.Heap(a, s, o, data[o:o + s]))

    stk = list()
    for (a, s) in mstk:
        o = _ofa(seg, a)
        stk.append(segments.Stack(a, s, o, data[o:o + s]))

    pd = list()
    for (a, s) in mpd:
        o = _ofa(seg, a)
        pd.append(segments.PrivateData(a, s, o, data[o:o + s]))

    return MemoryDump(dumpfile, mod, hp, stk, pd, seg, data)


def address_from_offset(dump, offset):
    '''
    Return the virtual address corresponding to an offset in
    the memory dump.
    '''
    return _address_from_offset(dump.segments, offset)


def offset_from_address(dump, address):
    '''
    Return the offset in the memory dump corresponding to a
    virtual address.
    '''
    return _offset_from_address(dump.segments, address)


def extract_segment_by_address(dump, address):
    '''Extracts a segment from the memory dump.
    '''
    for s in dump.segments:
        if s.address == address:
            logging.debug('Segment {:#08x} found'.format(address))
            with open('{}-{:#08x}.core'.format(dump.name, address), 'wb') as f:
                f.write(s.data)
            return True
    else:
        logging.debug('Segment {:#08x} not present'.format(address))
        return False


# internal functions

def _address_from_offset(segments, offset):
    '''
    Return the virtual address corresponding to an offset in
    the memory dump.
    '''
    temp_offset = 0
    for s in segments:
        if temp_offset + s.size >= offset:
            return s.address + offset - temp_offset
        else:
            temp_offset += s.size
    raise ValueError(
        'No corresponding address for offset: {:#08x}'.format(offset))


def _offset_from_address(segments, address):
    '''
    Return the offset in the memory dump corresponding to a
    virtual address.
    '''
    temp_offset = 0
    for s in segments:
        if s.address <= address:
            if s.address + s.size >= address:
                return temp_offset + address - s.address
            else:
                temp_offset += s.size
        else:
            raise ValueError(
                'No corresponding offset for address: {:#08x}'.format(address))


def _read_memory_dump_data(dumpfile):
    with open(dumpfile, 'rb') as f:
        return f.read()

# TODO: does NOT requires txt
# def _read_metadata(mdtype, dumpfile):
#     '''
#     Read segments of the specified type from file "dumpfile".
#     '''
#     with open(dumpfile, 'r') as f:
#         segments = list()
#         for line in f:
#             if mdtype == _SegmentType.Module:
#                 segments.append((int(line.split(':')[0], 16),
#                                                 int(line.split(':')[1], 16),
#                                                 line.split(':')[2].rstrip()))
#             elif mdtype == _SegmentType.Heap:
#                 segments.append((int(line.split(':')[0], 16),
#                                                 int(line.split(':')[1], 16)))
#             elif mdtype == _SegmentType.Pdata:
#                 segments.append((int(line.split()[0], 16),
#                                 int(line.split()[4].replace(',', '')) * 1024))
#             elif mdtype == _SegmentType.Stack:
#                 segments.append((int(line.split()[0], 16),
#                                  int(line.split()[4].replace(',', '')) * 1024))
#             else:  # mdtype == _SegmentType.Segment
#                 segments.append((int(line.split(':')[0], 16),
#                                                 int(line.split(':')[1], 16)))
#     return segments


# TODO: requires txt
def _read_metadata(mdtype, dumpfile):
    '''
    Read segments of the specified type from file "dumpfile".
    '''
    with open(dumpfile, 'r') as f:
        segments = list()
        for line in f:
            if mdtype == _SegmentType.Module:
                segments.append((int(line.split(':')[0], 16),
                                 int(line.split(':')[1], 16),
                                 line.split(':')[2].rstrip()))
            elif mdtype == _SegmentType.Heap:
                segments.append((int(line.split()[0], 16),
                                 int(line.split()[5].replace(',', '')) * 1024))
            elif mdtype == _SegmentType.Pdata:
                segments.append((int(line.split()[0], 16),
                                 int(line.split()[4].replace(',', '')) * 1024))
            elif mdtype == _SegmentType.Stack:
                segments.append((int(line.split()[0], 16),
                                 int(line.split()[4].replace(',', '')) * 1024))
            else:  # mdtype == _SegmentType.Segment
                segments.append((int(line.split(':')[0], 16),
                                 int(line.split(':')[1], 16)))
    return segments


_afo = _address_from_offset
_ofa = _offset_from_address


def _process_cmd_line(argv):
    '''Memory dump analysis.

Usage:
    memorydump.py [-v] <dump>
    memorydump.py convert [-v] <dump> (-a <address> | -o <offset>)
    memorydump.py extract [-v] <dump> -a <address>
    memorydump.py (-h | --version)

Options:
    -a <address>  Virtual address to convert.
    -o <offset>   Offset to convert.
    -h --help     Shows this message.
    -v --verbose  Shows details.
    --version     Shows the current version.
    '''
    # initializing the parser object
    args = docopt(_process_cmd_line.__doc__, argv=argv, version=__version__)

    # checking arguments
    try:
        if args['-a']:
            args['-a'] = int(args['-a'], 0)
    except ValueError:
        print('Error: Invalid address', args['-a'], file=sys.stderr)
        sys.exit(1)

    try:
        if args['-o']:
            args['-o'] = int(args['-o'], 0)
    except ValueError:
        print('Error: Invalid offset', args['-o'], file=sys.stderr)
        sys.exit(1)

    if args['--verbose']:
        print(args)
    return (args['<dump>'], args['-a'], args['-o'], args['convert'],
            args['extract'], args['--verbose'])


def main(argv=None):
    (dumpfile, address, offset, convert, extract,
     verbose) = _process_cmd_line(argv)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    dump = load_memory_dump(dumpfile)

    if convert:
        try:
            if address:
                o = offset_from_address(dump, address)
                print('Address: {:#08x} ==> offset: {:#08x}'.format(address,
                                                                    o))

            if offset or offset == 0:
                a = address_from_offset(dump, offset)
                print('Offset: {:#08x} ==> address: {:#08x}'.format(offset, a))
        except Exception as e:
            logging.error(e)
            return 1
    elif extract:
        if extract_segment_by_address(dump, address):
            print('Segment {:#08x} extracted'.format(address))
        else:
            print('Segment {:#08x} not found'.format(address))
    else:
        print(dump)

    return 0


if __name__ == '__main__':
    sys.exit(main())
