#!/usr/bin/env python

"""List dependencies of C files. Used in the makefile."""

import re
import sys
import glob

pat = re.compile('^\#include\s*"(.+)"', re.MULTILINE)

for file in glob.glob('*.c'):
    print '%s.o:' % file[:-2],
    for dep in pat.findall(open(file).read()): 
        print dep,
    print
