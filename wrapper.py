#!/usr/bin/python
# Copyright (c) 2010 TurnKey Linux - all rights reserved
"""Maintain a pool of packages from source and binary stocks

Environment variables:
    POOL_DIR            Location of pool (defaults to `.')
    DEBINFO_DIR         Location of debinfo cache (default: $HOME/.debinfo)
"""

from os.path import *
import pyproject

class CliWrapper(pyproject.CliWrapper):
    DESCRIPTION = __doc__
    
    INSTALL_PATH = dirname(__file__)

    COMMANDS_USAGE_ORDER = ['init',
                            '',
                            'register', 'unregister', 'info', 'info-build',
                            '',
                            'exists', 'list', 'get',
                            '',
                            'gc']

if __name__ == '__main__':
    CliWrapper.main()
