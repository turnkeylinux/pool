"""
This module includes convenience functions for handling Debian
binary packages.
"""
import re
import commands
import os.path

class Error(Exception):
    pass

def extract_control_fields(path):
    """extract control fields from a Debian binary package -> dict"""
    command = "ar -p %s control.tar.gz | zcat | tar -O -xf - ./control 2>/dev/null" % path
    error, output = commands.getstatusoutput(command)
    if error:
        raise Error("failed to extract control file with `%s`" % command)

    control = output
    return dict([ re.split("\s*:\s+", line.strip(), 1)
                  for line in control.split("\n")
                  if line.strip() and not line.startswith(" ") ])

