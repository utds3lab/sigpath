#!/usr/bin/env python
"""
Created on May 2, 2013

@author: David I. Urbina
"""

# imports
from __future__ import print_function
from bisect import bisect_left
import logging
import struct
import sys

from docopt import docopt
import networkx as nx

from segments import Segment
import memorydump


# constants

__version__ = 2.0
_ALLOC_UNIT_SZ_ = 8
_WORD_SZ_ = 4
_HEAP_SEG_ = 64
_USERM_INIT = 0x10000
_KERNEM_INIT = 0x80000000

_ofa = memorydump.offset_from_address
_afo = memorydump.address_from_offset

# exception classes


# interface classes

class DataStructure(Segment):
    def __init__(self, address, size, offset, data):
        super(DataStructure, self).__init__(address, size, offset, data)

    def __cmp__(self, other):
        return cmp(self.address, other.address)


class Pointer(object):
    def __init__(self, src, dest, offset_src, offset_dest):
        self.src = src
        self.dest = dest
        self.offset_src = offset_src
        self.offset_dest = offset_dest

    def __repr__(self):
        return '<p s={} d={} os={:#x} od={:#x}>'.format(self.src, self.dest,
                                                        self.offset_src, self.offset_dest)

    def __str__(self):
        return '{:#x}:{:#x}'.format(self.offset_src, self.offset_dest)


class MemoryGraph(nx.DiGraph):
    '''Represents a memory graph form by data structures and pointers.
    '''

    def seek_node_by_address(self, address):
        for n in self.nodes():
            if n.address == address:
                return n


# interface functions

def export_memory_graph(filename, graph):
    nx.write_dot(graph, '{}.dot'.format(filename))
    logging.debug('{}.dot created'.format(filename))


def generate_graph(dump):
    """Builds a graph for the memory data structures present
    in a memory dump. It roots the graph in the modules and
    the stacks.

    Returns the memory graph.
    """
    graph = MemoryGraph()
    data_structures = _parse_all_data_structures(dump)
    logging.debug('{} Data structures parsed'.format(len(data_structures)))
    graph.add_nodes_from(data_structures, color='orange', style='filled')
    global_pointers = _find_global_pointers(dump, data_structures)
    logging.debug('{} Global pointers found'.format(len(global_pointers)))
    stack_pointers = _find_stack_pointers(dump, data_structures)
    logging.debug('{} Stack pointers found'.format(len(stack_pointers)))
    ds_pointers = _find_data_structure_pointers(data_structures)
    logging.debug('{} Data structure pointers found'.format(len(ds_pointers)))
    graph.add_edges_from([(p.src, p.dest, {'label': p})
                          for p in global_pointers])
    graph.add_edges_from([(p.src, p.dest, {'label': p})
                          for p in stack_pointers])
    graph.add_edges_from([(p.src, p.dest, {'label': p})
                          for p in ds_pointers])
    graph.add_nodes_from(dump.modules, color='blue', style='filled')
    graph.add_nodes_from(dump.stacks, color='purple', style='filled')
    graph.root_nodes = list(set(dump.modules) | set(dump.stacks))
    sizeg = sum([n.size for n in graph.nodes()])
    removed = _remove_unreachable_nodes(graph)
    sizeg2 = sum([n.size for n in graph.nodes()])
    logging.debug("Sizes (KB): {} {} {}".format(dump.size / 1024, sizeg / 1024, sizeg2 / 1024))
    logging.debug('{} Unreachable nodes removed'.format(removed))
    logging.debug('{} #nodes - {} #edges'.format(len(graph.nodes()),
                                                 len(graph.edges())))
    return graph


# internal classes

class _HeapEntryFlags:
    USED = 0x01
    END = 0x10


# internal functions

def _parse_all_data_structures(dump):
    """Parses the Heap segments present in the memory dump
    and creates a list of allocated data structures.
    """
    data_structures = []
    for heap in dump.heaps:
        data_structures.extend(_parse_heap_data_structures(dump, heap))

    return data_structures


def _parse_heap_data_structures(dump, heap):
    data_structures = list()
    for i in xrange(heap.offset + 0x58, heap.offset + 0x58 +
            (_HEAP_SEG_ * _WORD_SZ_), _WORD_SZ_):
        seg_address = struct.unpack('<I', dump.data[i:i + _WORD_SZ_])[0]
        if seg_address != 0:
            seg_offset = _ofa(dump, seg_address)
            heap_entries = _parse_heap_segment_entries(dump, seg_offset)
            data_structures.extend(
                [DataStructure(_afo(dump, o), s, o, dump.data[o: o + s])
                 for (o, s) in heap_entries])
        else:
            break
    return data_structures


def _parse_heap_segment_entries(dump, segment_offset):
    """Parse all the HEAP_ENTRY's starting at the given offset
    and appends a new data structure per HEAP_ENTRY.
    """
    fe = struct.unpack('<I',
                       dump.data[segment_offset + 0x20: segment_offset + 0x20 + 4])[0]
    feo = _ofa(dump, fe)
    heap_entries = []
    last = False
    while not last:
        # current size
        csize = struct.unpack('<H', dump.data[feo:feo + 2])[0]
        # previous size
        #         psize = struct.unpack('<H', dump.data[feo + 2:feo + 4])[0
        # flags
        flags = struct.unpack('<B', dump.data[feo + 5:feo + 6])[0]
        # unused bytes
        ubytes = struct.unpack('<B', dump.data[feo + 6:feo + 7])[0]
        # data structure offset
        offset = feo + _ALLOC_UNIT_SZ_
        # data structure size
        size = (csize * _ALLOC_UNIT_SZ_) - ubytes
        if flags & _HeapEntryFlags.USED:
            heap_entries.append((offset, size))
        feo += csize * _ALLOC_UNIT_SZ_
        last = flags & _HeapEntryFlags.END
    return heap_entries


def _search_data_structure_with_address(data_structures, address):
    """Implements binary search over the list of data structures.
    """
    index = bisect_left(data_structures, DataStructure(address, 0, 0, []))
    ds = data_structures[index - 1]
    if ds.address <= address < ds.address + ds.size:
        return ds
    if index < len(data_structures):
        ds = data_structures[index]
        if ds.address <= address < ds.address + ds.size:
            return ds


def _find_global_pointers(dump, data_structures):
    """Returns the list of global pointers making use of
    the global ranges.
    """
    global_pointers = list()
    sorted(data_structures, key=lambda ds: ds.address)
    for m in dump.modules:
        for (w, o) in m.walk_by_word():
            if _USERM_INIT <= w < _KERNEM_INIT:
                ds = _search_data_structure_with_address(data_structures, w)
                if w % _WORD_SZ_ == 0 and ds:
                    global_pointers.append(Pointer(m, ds, o, w - ds.address))
    return global_pointers


def _find_stack_pointers(dump, data_structures):
    """Returns the list of stack pointers making use of
    the stack ranges.
    """
    stack_pointers = list()
    for s in dump.stacks:
        for (w, o) in s.walk_by_word():
            if _USERM_INIT <= w < _KERNEM_INIT:
                ds = _search_data_structure_with_address(data_structures, w)
                if w % _WORD_SZ_ == 0 and ds:
                    stack_pointers.append(Pointer(s, ds, o, w - ds.address))
    return stack_pointers


def _find_data_structure_pointers(data_structures):
    """Returns the list of stack pointers making use of
    the stack ranges.
    """
    ds_pointers = list()
    for ds in data_structures:
        for (w, o) in ds.walk_by_word():
            if _USERM_INIT <= w < _KERNEM_INIT:
                ds2 = _search_data_structure_with_address(data_structures, w)
                if w % _WORD_SZ_ == 0 and ds2 and ds != ds2:
                    ds_pointers.append(Pointer(ds, ds2, o, w - ds2.address))
    return ds_pointers


def _remove_unreachable_nodes(graph):
    """Remove all data structures that are not reachable
    from modules or from stacks.
    """
    removed = 0
    for node in graph.nodes()[:]:
        # check if reachable from globals
        for root in graph.root_nodes:
            if nx.has_path(graph, root, node):
                break
        else:
            graph.remove_node(node)
            removed += 1
    return removed


def _process_cmd_line(argv):
    """Memory graph generator.

Usage:
    graph_generator.py [--verbose] <dump>
    graph_generator.py (--help | --version)

Options:
    <dump>        The memory dump file.
    -h --help     Shows this message.
    -v --verbose  Shows details.
    --version     Shows the current version.
    """
    # initializing the parser object
    args = docopt(_process_cmd_line.__doc__, argv=argv, version=__version__)

    # checking arguments
    if args['--verbose']:
        print(args)
    return args['<dump>'], args['--verbose']


def main(argv=None):
    dumpfile, verbose = _process_cmd_line(argv)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    try:
        dump = memorydump.load_memory_dump(dumpfile)
    except Exception as e:
        logging.error(e)
    logging.debug(dump)
    graph = generate_graph(dump)
    export_memory_graph(dump.name, graph)
    return 0


if __name__ == '__main__':
    sys.exit(main())
