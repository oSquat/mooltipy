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

"""Manage mooltipass settings."""

import argparse
import os
import sys
import logging
import time

from mooltipy.mooltipass_client import MooltipassClient

def get_param(mooltipass, args):
    value = mooltipass.get_param(mooltipass.valid_params[args.param])
    print("Current value of {}: {}".format(args.param, value))

def set_param(mooltipass, args):
    success = mooltipass.set_param(mooltipass.valid_params[args.param], int(args.value))
    if success != 1:
        print("Failed to set parameter {} to {}".format(mooltipass.valid_params[args.param], args.value))

def main_options():
    """Handles command-line interface, arguments & options. """

    # If the wrapper was used to execute our utility instead of directly
    util = ''
    if os.path.split(sys.argv[0])[1] in ['./mooltipy.py', 'mooltipy']:
        # Get the utility name contained in argv[1]
        util = sys.argv[1]
        del sys.argv[1]

    # Create a string to represent the utility in help messages
    cmd_util = (' '.join([os.path.split(sys.argv[0])[1], util])).strip()

    description = '{cmd_util} manages Mooltipass login contexts.'.format(
            cmd_util = cmd_util)
    usage = '{cmd_util} [-h] ... {{get,set,del}} context'.format(
            cmd_util = cmd_util)

    # main
    parser = argparse.ArgumentParser(usage = usage, description=description)
    # TODO: Necessary -q -v -f options? Maybe with read / delete.
    #parser.add_argument('-q','--quiet', action='store_true',
    #        help='suppress output and warnings)

    # subparser
    subparsers = parser.add_subparsers(
            dest = 'command', help='action to take on context')

    # get
    # ---
    get_parser = subparsers.add_parser(
            'get',
            help = 'Get a favorite or favorites',
            prog = cmd_util+' get')
    get_parser.add_argument("param", help='Which parameter to get', choices=MooltipassClient.valid_params.keys())

    # set
    # ---
    set_parser = subparsers.add_parser(
            'set',
            help = 'Set or update a favorite',
            prog = cmd_util+' set')
    set_parser.add_argument("param", help='Which parameter to set', choices=MooltipassClient.valid_params.keys())
    set_parser.add_argument("value", help='Value to set for a parameter')

    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    return args

def main():

    command_handlers = {
        'get':get_param,
        'set':set_param,
    }

    args = main_options()

    mooltipass = MooltipassClient()

    try:
        pass
    except Exception as e:
        print(e)
        sys.exit(1)

    # Ping the mooltipass, an integral part of the initialization process.
    if not mooltipass.ping():
        print('Mooltipass did not reply to a ping request!')
        sys.exit(1)

    # Ensure Mooltipass status
    quiet_bool = False
    while True:
        status = mooltipass.get_status()
        if status == 5:
            break
        if not quiet_bool:
            print('Insert a card and unlock the Mooltipass...')
        quiet_bool = True
        time.sleep(1)
    quiet_bool = False

    command_handlers[args.command](mooltipass, args)

    sys.exit(0)

if __name__ == '__main__':

    main()
