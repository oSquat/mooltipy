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

"""Manage contexts containing usernames & passwords."""

import argparse
import os
import time
import sys

from mooltipy.mooltipass_client import MooltipassClient

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

    description = '{cmd_util} manages Mooltipass login contexts.'.format(cmd_util = cmd_util)
    usage = '{cmd_util} [-h] [-f] [-q] ... {{get,set,del}} context'.format(cmd_util = cmd_util)

    # main
    parser = argparse.ArgumentParser(usage = usage, description=description)
    #parser.add_argument('-q','--quiet', action='store_true', help='suppress output and warnings)
    #parser.add_argument('-v','--verbose', action='store_true', help='turn on verbosity')

    # subparser
    subparsers = parser.add_subparsers(
            dest = 'command', help='action to take on context')

    # get
    # ---
    get_parser = subparsers.add_parser(
            'get',
            help = 'Get a password for given context',
            prog = cmd_util+' get')
    get_parser.add_argument("context", help='specify context (e.g. Lycos.com)')

    # set
    # ---
    set_parser = subparsers.add_parser(
            'set',
            help = 'Set or update a context',
            prog = cmd_util+' set')
    set_parser.add_argument('-u','--username',
            help = 'optional username for the context',
            default = '',
            action = 'store')
    set_parser.add_argument(
            '-p','--password',
            help = 'do not set this option to generate a random password ' + \
                   '(best method); set this option without specifying a ' + \
                   'password to be promted at runtime (ok method); avoid ' + \
                   'setting this option and specifying the password on the ' + \
                   'command line (terrible option)',
            nargs = '?',
            action = 'store')
    set_parser.add_argument(
            '-l', '--length',
            help = 'specify maximum password length; default is the ' + \
                   'maximum of 31 characters minus appended character',
            nargs = '?',
            type = int,
            action='store')
    set_parser.add_argument(
            '-s', '--skip',
            help = 'password characters that can not be used',
            nargs='?',
            action='store')
    set_parser.add_argument(
            '-au',
            help = 'Append to the Username a tab or crlf',
            action = 'store',
            choices = ['tab','crlf'])
    set_parser.add_argument(
            '-ap',
            help = 'Append to the Password a tab or crlf',
            action = 'store',
            choices = ['tab','crlf'])
    set_parser.add_argument("context", help='specify context (e.g. Lycos.com)')

    # delete
    # ------
    del_parser = subparsers.add_parser(
            'del',
            help='Delete a context',
            prog=cmd_util+' del')
    del_parser.add_argument("context", help='specify context (e.g. Lycos.com)')

    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    return args

def get_context(mooltipass, args):
    print('Not yet implemented.')
    sys.exit(1)

def set_context(mooltipass, args):

    if not args.password:
        print('Automatic password generation not yet implemented.')
        sys.exit(1)

    # TODO: validate username / password lengths

    append = {
        'tab':b'\x09',
        'crlf':b'\x0d',
        None:''
    }

    args.username += append[args.au]
    args.password += append[args.ap]

    while not mooltipass.set_context(args.context):
        mooltipass.add_context(args.context)

    if args.username:
        uname_ret = mooltipass.set_login(args.username)
    else:
        uname_ret = mooltipass.set_login('')

    if not uname_ret:
        print('Set username failed!')
        sys.exit(1)

    if not mooltipass.set_password(args.password):
        print('Set password failed!')
        sys.exit(1)


def del_context(mooltipass, args):
    print('Not yet implemented.')
    sys.exit(1)

def main():

    command_handlers = {
        'get':get_context,
        'set':set_context,
        'del':del_context
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
        time.sleep(2)
    quiet_bool = False

    command_handlers[args.command](mooltipass, args)
    sys.exit(0)

if __name__ == '__main__':

    main()

    # TODO: Crucial
    #   * Random password generation
    #   * Prompt for password if not specified
    #   * Input validation
    # TODO: Important
    #   * Implement get
    #   * Canceling request to add context loops and can't be terminated.
    #   * Call .check_password() before setting password to avoid superfluous
    #     prompting of the user.
    #   * Implement --length and --skip
    # TODO: Eventually
    #   * Implement delete
