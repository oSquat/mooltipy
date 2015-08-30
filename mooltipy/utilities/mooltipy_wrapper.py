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

# README:
# This file is a hectic wrapper. If you're looking to understand a
# particular utility, it would be best if you viewed that utility under
# the utilities directory -- see /mooltipy/utilities/mp*.py

import argparse
import sys

from mooltipy.utilities import mpdata
from mooltipy.utilities import mplogin

# Dictionary key:values == "utility name": module
#   Used to print out usage and as a switch/case to branch on chosen
#   utility. Entrypoint is assumed to be main() and the description
#   of what the utility does is pulled from the module's docstring.
utilities = {
    'data': mpdata,
    'login': mplogin,
}

def main_options():
    """Handles command-line interface, arguments & options."""

    utility_list = ''
    for key, value in utilities.items():
        utility_list += ' '*7 + key.upper() + '\t- ' + value.__doc__ + '\n'

    usage = 'Usage: %(prog)s UTILITY <utility arguments & options>\n' + \
            'Avalilable utilities:\n' + \
            utility_list

    # This is a wormhole to pass help flags onto the utility specified
    # instead of leaving them for our wrapper's parse_args() to find.
    utility_help = False
    if len(sys.argv) > 2 and (set(['-h','--help', 'help']) & set(sys.argv)):
        help_string = (set(['-h','--help', 'help']) & set(sys.argv)).pop()
        utility_help = True
        help_index = sys.argv.index(help_string)
        sys.argv[help_index] = None

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('utility', help='Utility to use.')
    parser.add_argument('args', help='Arguments & options to pass onto utility.',
            nargs='+')

    args = parser.parse_args()

    if not args.utility.lower() in utilities.keys():
        parser.print_help()
        sys.exit(1)

    # Pass --help onto utility if help was asked of a utility.
    if utility_help:
        sys.argv[help_index] = '--help'

    return args

def main():

    args = main_options()
    utilities[args.utility.lower()].main()

if __name__ == '__main__':
    main()

    # TODO:
    #   * Providing no argument list to utility results in
    #       mooltipy_wrapper's help displaying, not the utilities.
    #       E.g. $ mooltipy data
    #           should show mpdata help dialog, not wrapper's
