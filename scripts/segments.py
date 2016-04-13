#!/usr/bin/env python
"""
Created on May 2, 2013

@author: David I. Urbina
"""

# imports
import math
import struct
import logging
# constants
_WORD_SIZE = 4
# exception classes
# interface functions


# interface classes

class Segment(object):
    def __init__(self, address, size, offset=None, data=None):
        self.address = address
        self.size = size
        self.offset = offset
        self.data = data
        self.data = [] if data is None else data
        self.type = type(self).__name__
        self.hash = None

    def __repr__(self):
        if self.offset or self.offset == 0:
            return '<{} a={:#08x} s={} o={:#08x}>'.format(self.type,
                                                          self.address, self.size, self.offset)
        else:
            return '<{} a={:#08x} s={}>'.format(self.type, self.address,
                                                self.size)

    def __str__(self):
        return '{:#08x}({})'.format(self.address, self.size)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        if self.hash == None:
            self.hash = hash(repr(self.address) + repr(self.size) +
                             repr(self.data))
        return self.hash

    def walk_by_word(self):
    #         logging.debug('Walking {}'.format(self.__class__))
        from_ = 0
        to_ = math.trunc(self.size / _WORD_SIZE) * _WORD_SIZE
        step = _WORD_SIZE
        for i in xrange(from_, to_, step):
            yield struct.unpack('<I', self.data[i:i + _WORD_SIZE])[0], i

    def walk_by_byte(self):
        for i in xrange(self.size - 1):
            yield self.data[i], i


class Module(Segment):
    def __init__(self, name, address, size, offset, data):
        super(Module, self).__init__(address, size, offset, data)
        self.name = name

    def __str__(self):
        return '{}({})'.format(self.name, self.size)

    def __repr__(self):
        return '<{} n={} a={:#08x} s={}>'.format(self.type, self.name,
                                                 self.address, self.size)


class Heap(Segment):
    def __init__(self, address, size, offset, data):
        super(Heap, self).__init__(address, size, offset, data)


class Stack(Segment):
    def __init__(self, address, size, offset, data):
        super(Stack, self).__init__(address, size, offset, data)

    def walk_by_word(self):
        logging.debug('Walking {}'.format(self.__class__))
        from_ = self.size - _WORD_SIZE
        to_ = self.size - math.trunc(self.size / _WORD_SIZE) * _WORD_SIZE
        step = -_WORD_SIZE
        for i in xrange(from_, to_, step):
            yield (struct.unpack('<I', self.data[i:i + _WORD_SIZE])[0],
                   self.size - i)

    def walk_by_byte(self):
        for i in xrange(self.size - 1, 0, -1):
            yield self.data[i], self.size - i


class PrivateData(Segment):
    def __init__(self, address, size, offset, data):
        super(PrivateData, self).__init__(address, size, offset, data)

# internal functions
# internal classes
