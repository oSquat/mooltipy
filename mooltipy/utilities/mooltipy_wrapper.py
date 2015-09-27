#!/usr/bin/env python
#
# This file is part of Mooltipy.
#
# Mooltipy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mooltipy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mooltipy.  If not, see <http://www.gnu.org/licenses/>.

"""Wraps all utilities under a mooltipy command."""

import argparse
import sys

from mooltipy.utilities import mpdata
from mooltipy.utilities import mplogin
from mooltipy.utilities import mpfavorites
from mooltipy.utilities import mpparams

utilities = {
    'data': mpdata,
    'login': mplogin,
    'favorites': mpfavorites,
    'parameters': mpparams,
}

def main_options():
    """Handles command-line interface, arguments & options."""

    utility_list = ''
    for key, value in utilities.items():
        utility_list += ' '*7 + key.upper() + '\t- ' + value.__doc__ + '\n'

    usage = 'Usage: %(prog)s UTILITY <utility arguments & options>\n' + \
            'Avalilable utilities:\n' + \
            utility_list

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('utility', help='Utility to use.')
    parser.add_argument('args', help='Arguments & options to pass onto utility.',
            nargs=argparse.REMAINDER)

    args = parser.parse_args()

    # Alias some utilities
    if args.utility in ['params']:
        args.utility = 'parameters'

    if not args.utility.lower() in utilities.keys():
        parser.print_help()
        sys.exit(1)

    return args

def main():

    args = main_options()
    utilities[args.utility.lower()].main()

if __name__ == '__main__':
    main()
