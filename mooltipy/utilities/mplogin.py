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
import fnmatch
import getpass
import logging
import os
import sys
import time

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

    description = '{cmd_util} manages Mooltipass login contexts.'.format(
            cmd_util = cmd_util)
    usage = '{cmd_util} [-h] ... {{get,set,del,list}} context'.format(
            cmd_util = cmd_util)

    # main
    parser = argparse.ArgumentParser(usage = usage, description=description)

    parser.add_argument('-smx', '--skip_mgmt_exit',
                        help='Skip exiting management mode',
                        action='store_true')

    # subparser
    subparsers = parser.add_subparsers(
            dest = 'command', help='action to take on context')

    # get
    # ---
    description = 'Return the password through stdout for a given context & ' \
            'login.'
    get_parser = subparsers.add_parser(
            'get',
            help = 'get a password for given context',
            description = description,
            prog = cmd_util+' get')
    # TODO: accept username as an argument
    get_parser.add_argument('-u','--username',
            help = 'optional username for the context',
            default = '',
            action = 'store')
    get_parser.add_argument("context", help='specify context (e.g. Lycos.com)')
    get_parser.add_argument(
        '-w', '--with-username',
        help = 'Return username on first line, password on second.',
        dest = 'with_username',
        default = False,
        action = 'store_true')
    get_parser.add_argument(
        '-c', '--with-context',
        help = 'Implies --with-username. Return context on first line, username on second line and password on third.',
        dest = 'with_context',
        default = False,
        action = 'store_true')

    # set
    # ---
    description = 'Create or modify a login context (e.g. credentials for example.com).\n\n' \
            'Examples:\n' \
            '\t# Set a random passord for user_name at the example.com context' \
            '\n\t$ {cmd_util} set login example.com -u user_name\n\n' \
            '\t# Set an alphanumeric password for user_name at the example.com context' \
            '\n\t$ {cmd_util} set login example.com -u user_name -c alnum\n\n' \
            '\t# Set a password for user_name, but ask for it at runtime ' \
            '\n\t$ {cmd_util} set login example.com -u user_name -p\n\n' \
            '\t# Specify a password for user_name on the command line (bad idea)' \
            '\n\t$ {cmd_util} set login example.com -u user_name -p "P@ssw0rd"'

    set_parser = subparsers.add_parser(
            'set',
            help = 'set or update a context',
            description = description.format(cmd_util=cmd_util),
            formatter_class = argparse.RawDescriptionHelpFormatter,
            prog = cmd_util+' set')
    set_parser.add_argument('-u','--username',
            help = 'optional username for the context',
            default = '',
            action = 'store')
    set_parser.add_argument(
            '-p','--password',
            help = 'do not set this option to generate a random password ' + \
                   '(best method); set this option without specifying a ' + \
                   'password to be prompted at runtime for the password (ok ' + \
                   'method); set this option and specify a password at the ' + \
                   'same time on the command line (terrible method unless ' + \
                   'you\'re scripting)',
            nargs = '?',
            default = None,             # Set if -p not present
            const = '',                 # Set if -p present with no argument
            action = 'store')
    set_parser.add_argument(
            '-l', '--length',
            help = 'specify maximum password length if generating a random ' + \
                   'password; default is the maximum of 31 characters ' + \
                   'appended character',
            nargs = '?',
            type = int,
            default = 31,
            action = 'store')
    set_parser.add_argument(
            '-c', '--charset',
            help = 'character set for use in random password generation ' + \
                   'you can currently use {an|alnum|alphanumeric} to only ' + \
                   'use alpha-numeric values',
            nargs='?',
            default = None,
            action='store')
    set_parser.add_argument(
            '-au',
            help = 'append to the Username a tab or crlf',
            action = 'store',
            choices = ['tab','crlf'])
    set_parser.add_argument(
            '-ap',
            help = 'append to the Password a tab or crlf',
            action = 'store',
            choices = ['tab','crlf'])
    set_parser.add_argument("context", help='specify context (e.g. geocities.com)')

    # delete
    # ------
    description = 'Delete a context or specific login from a context.'
    del_parser = subparsers.add_parser(
            'del',
            help='delete a context',
            description = description,
            prog = cmd_util+' del')
    del_parser.add_argument('-u','--username',
            help = 'optional username for the context',
            default = '',
            action = 'store')
    del_parser.add_argument("context", help='specify context (e.g. tripod.com)')

    # list
    # ----
    description = 'List login contexts contained in the mooltipass.'
    list_parser = subparsers.add_parser(
            'list',
            help = 'list login contexts',
            description = description,
            prog = cmd_util+' list')
    list_parser.add_argument(
            'context',
            action = 'store',
            default = '*',
            nargs = '?',
            help = 'supports shell-style wildcards; default is "*" showing all contexts.')
    list_parser.add_argument(
        '-D', '--DANGER-REVEAL-MY-PASSWORDS',
        help = 'DANGER: THIS OPTION REVEALS ALL YOUR PASSWORDS IN CLEAR. USE WISELY! OR BETTER, DO NOT USE IT',
        dest = 'with_passwords',
        default = False,
        action = 'store_true')
    list_parser.add_argument(
        '-d', '--dump',
        help = 'List contexts and passwords in a way which would be simpler to parse by external tools.',
        default = False,
        action = 'store_true')



    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    # end subparsers
    args = parser.parse_args()

    if args.command == 'set':
        if args.charset is not None and \
                args.charset in ['an', 'alnum', 'alphanum', 'alphanumeric']:
            args.charset = 'an'

        # Ask for password if -p was specified
        if args.password != None and len(args.password) == 0:
            args.password = getpass.getpass('Enter the password to use:')

    return args

def get_context(mooltipass, args):
    """Get a password for a given context."""
    set_context = mooltipass.set_context(args.context)
    if set_context == False:
        raise RuntimeError('Context unknown. Use list action to see available contexts')
    if set_context is None:
        raise RuntimeError('Unlock the mooltipass and try again.')

    # Try to get password; 0 means there are multiple logins for this context
    # and that --username was not used to specify which one to pick
    username = mooltipass.get_login(args.username)
    password = mooltipass.get_password()
    if password == 0:
        username = mooltipass.get_login(args.username)
        password = mooltipass.get_password()

    if args.with_context:
        print(args.context)
    if args.with_username or args.with_context:
        print(username.decode())
    print(password.decode())

def list_context(mooltipass, args):
    """List login contexts"""
    mooltipass.start_memory_management()

    if args.with_passwords:
        s = '{:<70}{:<70}{:<70}\n'.format('Context:','Login(s):','Password(s):')
    else:
        s = '{:<70}{:<70}\n'.format('Context:','Login(s):')
    s += '{:<70}{:<70}\n'.format('--------','---------')
    if args.dump:
        s = ''
    for pnode in mooltipass.parent_nodes('login'):
        if fnmatch.fnmatch(pnode.service_name.decode(), args.context):
            service_name = pnode.service_name.decode()
            context = service_name
            for cnode in pnode.child_nodes():
                username = cnode.login.decode()
                if args.with_passwords:
                    mooltipass.set_context(context)
                    mooltipass.get_login(username)
                    retpassword = mooltipass.get_password()
                    s += '{:<70}{:<70}{:<70}\n'.format(service_name, username, retpassword.decode())
                else:
                    s += '{:<70}{:<70}\n'.format(service_name, username)
                if not args.dump:
                    service_name = ''

    print(s)
    if args.skip_mgmt_exit == False:
        mooltipass.end_memory_management()

def generate_random_password(args):
    """Generate and return a random password."""
    # TODO: Consider if passwords could stick around in memory after
    #   execution and how immutable vs mutable types could effect this.
    new_password = []
    while len(new_password) < args.length:
        char = chr((ord(os.urandom(1)) % (127 - 32)) + 32)
        if args.charset and 'an' in args.charset and not char.isalnum():
            continue
        new_password += char
    return ''.join(new_password)

def set_context(mooltipass, args):
    """Create context and add or update a username & set the password."""

    # Fixes if password length is at max 31 chars and appended char requested
    if args.ap and args.length == 31:
        args.length -= 1

    # Generate a random password if no -p argument specified
    if args.password is None:
        args.password = generate_random_password(args)

    # append tab/crlf to credentials
    append = {
        'tab':b'\x09',
        'crlf':b'\x0d',
        None:''
    }
    args.username += append[args.au]
    args.password += append[args.ap]

    if len(args.username) > 61:
        raise RuntimeError('Username must be <= 61 characters long!')

    if len(args.password) > 31:
        raise RuntimeError('Password must be <= 31 characters long!')

    # Set context and credentials
    while not mooltipass.set_context(args.context):
        if not mooltipass.add_context(args.context):
            raise RuntimeError('Request to add context denied or timed out.')

    if args.username:
        uname_ret = mooltipass.set_login(args.username)
    else:
        uname_ret = mooltipass.set_login('')

    if not uname_ret:
        raise RuntimeError('Set username failed!')

    # check_password really slows things down because of timer when
    # there isn't much harm in just asking the user to set the password.
    #if not mooltipass.check_password(args.password):
    if not mooltipass.set_password(args.password):
        raise RuntimeError('Set password failed!')

def del_context(mooltipass, args):
    """Delete a context in its entirety."""

    if not mooltipass.set_context(args.context):
        raise RuntimeError('That context ({}) does not exist.'.format(args.context))

    mooltipass.start_memory_management()

    for pnode in mooltipass.parent_nodes('login'):
        if pnode.service_name == args.context:
            if args.username:
                for cnode in pnode.child_nodes():
                    if cnode.login == args.username:
                        cnode.delete()
            else:
                pnode.delete()

    if args.skip_mgmt_exit == False:
        mooltipass.end_memory_management()

def main():

    logging.basicConfig(
            #format='%(levelname)s\t %(funcName)s():\t %(message)s',
            format='%(message)s',
            level=logging.INFO)

    command_handlers = {
        'get':get_context,
        'set':set_context,
        'del':del_context,
        'list':list_context
    }

    args = main_options()

    try:
        mooltipass = MooltipassClient()
    except Exception as e:
        print('An error occurred accessing the mooltipass: \n{}'.format(e))
        sys.exit(1)

    try:
        # Ensure Mooltipass status
        quiet_bool = False
        if not mooltipass.get_status() == 5:
            print('Insert a card and unlock the Mooltipass or cancel with ctrl-c')
            while True:
                if mooltipass.get_status() == 5:
                    break
                time.sleep(1)

        command_handlers[args.command](mooltipass, args)
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print('An error occurred: \n{}'.format(e))
    finally:
        print('')

if __name__ == '__main__':

    main()
