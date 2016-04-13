"""
Created on May 22, 2013

@author: David I. Urbina
"""
from __future__ import print_function
from datetime import datetime
import sys


def start_op(sstring='staring operations...', time=True):
    global tstart
    print(sstring, end=' ')
    sys.stdout.flush()
    if time:
        tstart = datetime.now()


def end_op(estring='READY'):
    global tstart
    if tstart:
        tend = datetime.now()
        print(estring, tend - tstart)
        tstart = None
    else:
        print(estring)
