#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Remove set versions of python dependencies from requirements.txt"""

import sys

for line in sys.stdin:
    python_dep = None

    splits = line.split(";")
    if len(splits) > 1:
        python_dep = splits[-1].strip()
    
    new_line = splits[0].split("=")[0].strip()
    
    if python_dep is not None:
        new_line += " ; " + python_dep
    
    sys.stdout.write(new_line + "\n")
