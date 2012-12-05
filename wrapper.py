#!/usr/bin/python
# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

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
