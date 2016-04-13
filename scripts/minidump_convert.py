#!/usr/bin/env python
"""
Created on Nov 26, 2012

@author: David I. Urbina
"""
from __future__ import print_function
import logging
import sys

from docopt import docopt

from minidump import *


# Constants
__version__ = 1.0

# Modules to exclude
# _STDLIB_EXC_ = []
_STDLIB_EXC_ = ['rpcrt4.dll', 'ole32.dll', 'advapi32.dll', 'user32.dll',
                'comctl32.dll', 'winmm.dll', 'secur32.dll', 'gdi32.dll',
                'gdiplus.dll', 'wininet.dll', 'crypt32.dll', 'msasn1.dll',
                'oleaut32.dll', 'shlwapi.dll', 'comdlg32.dll', 'shell32.dll',
                'winspool.drv', 'oledlg.dll', 'version.dll', 'riched32.dll',
                'riched20.dll', 'rsaenh.dll', 'clbcatq.dll', 'comres.dll',
                'shdocvw.dll', 'cryptui.dll', 'netapi32.dll', 'wintrust.dll',
                'imagehlp.dll', 'wldap32.dll', 'uxtheme.dll', 'xpsp2res.dll',
                'wtsapi32.dll', 'winsta.dll', 'imm32.dll', 'msimg32.dll',
                'apphelp.dll', 'ws2_32.dll', 'ws2help.dll', 'urlmon.dll',
                'setupapi.dll', 'msacm32.dll', 'sensapi.dll', 'oleacc.dll',
                'iphlpapi.dll', 'wsock32.dll', 'msls31.dl', 'psapi.dll',
                'sxs.dll', 'mlang.dll', 'simtf.dll', 'rasapi32.dll',
                'rasman.dll', 'tapi32.dll', 'rtutils.dll', 'shdoclc.dll',
                'jscript.dll', 'mswsock.dll', 'hnetcfg.dll', 'wshtcpip.dll',
                'dnsapi.dll', 'winrnr.dll', 'rasadhlp.dll', 'schannel.dll',
                'userenv.dll', 'dssenh.dll', 'perfos.dll', 'wdmaud.drv',
                'msacm32.drv', 'midimap.dll', 'msvcr100.dll', 'msvcp100.dll',
                'kernel32.dll', 'msvcrt.dll', 'ntdll.dll', 'mshtml.dll',
                'msctf.dll']

# Modules to include
_STDLIB_INCL_ = ['kernel32.dll', 'msvcrt.dll', 'ntdll.dll', 'mshtml.dll',
                 'msctf.dll']


def extract_core(filename, minidump):
    with open(filename, 'rb') as f:
        for s in minidump.MINIDUMP_DIRECTORY:
            if s.StreamType == 'Memory64ListStream':
                logging.debug('Extracting core...')
                with open(filename.replace('dmp', 'core'), 'w') as f2:
                    f2.write(f.read()[s.DirectoryData.BaseRva:])
                logging.info('Core extracted')
                return


def extract_segments(filename, minidump):
    for s in minidump.MINIDUMP_DIRECTORY:
        if s.StreamType == 'Memory64ListStream':
            logging.debug('Extracting segments...')
            with open(filename.replace('dmp', 'segments'), 'w') as f:
                for d in s.DirectoryData.MINIDUMP_MEMORY_DESCRIPTOR64:
                    value = '{:x}:{:x}\n'.format(d.StartOfMemoryRange,
                                                 d.DataSize)
                    f.write(value)
            logging.info('Segments extracted')
            return


def extract_modules(filename, minidump, all_mod):
    for s in minidump.MINIDUMP_DIRECTORY:
        if s.StreamType == 'ModuleListStream':
            logging.debug('Extracting modules...')
            with open(filename.replace('dmp', 'modules'), 'w') as f:
                for m in s.DirectoryData.MINIDUMP_MODULE:
                    if not all_mod and any(x in m.ModuleName.lower()
                                           for x in _STDLIB_EXC_):
                        continue
                    name = m.ModuleName.split('\\')[-1]
                    value = '{:x}:{:x}:{}\n'.format(m.BaseOfImage,
                                                    m.SizeOfImage, name)
                    f.write(value)
            logging.info('Modules extracted')
            return


def _process_cmd_line(argv):
    '''Minidump converter.

Usage:
    minidump_convert.py [options] <dump>
    minidump_convert.py (-h | --help | --version)

Options:
    <dump>        The minidump file.
    -m            Extract non-standard modules.
    -M            Extract all modules.
    -s            Extract segments.
    -c            Extract core.
    -v --verbose  Verbose.
    -h --help     Shows this help.
    --version     Shows the current version.
    '''
    # initializing the parser object
    args = docopt(_process_cmd_line.__doc__, argv=argv, version=__version__)

    return (args['<dump>'], args['-m'], args['-M'], args['-s'],
            args['-c'], args['--verbose'])


def main(argv=None):
    dumpfile, mod, allmod, seg, core, verbose = _process_cmd_line(argv)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    minidump = MINIDUMP_HEADER.parse_stream(open(dumpfile))

    if core:
        extract_core(dumpfile, minidump)
    if seg:
        extract_segments(dumpfile, minidump)
    if mod or allmod:
        extract_modules(dumpfile, minidump, allmod)
    return 0


if __name__ == '__main__':
    sys.exit(main())
