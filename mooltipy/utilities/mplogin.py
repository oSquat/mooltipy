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

from optparse import OptionParser
import os
import time
import sys

from mooltipy.mooltipass_client import MooltipassClient

def main_options():
    """Handles command-line interface, arguments & options. """

    # Fix usage message if executed from wrapper
    utility_called = ''
    print('utility called: ' + os.path.split(sys.argv[0])[1])
    if os.path.split(sys.argv[0])[1] in ['./mooltipy.py', 'mooltipy']:
        utility_called = sys.argv[1]
        del sys.argv[1]

    usage = 'Usage: %prog {utility} [OPTIONS]\n'.format(utility=utility_called)
    usage +='Example: %prog {utility} '.format(utility=utility_called)
    usage += 'Lycos.com --login=jsmith --password="not_random"'

    parser = OptionParser(usage)
    parser.add_option('--login', dest='login', metavar='USER',
            help='login for context')
    parser.add_option('--password', dest='password', metavar='PASS',
            help='password for login')

    (options, args) = parser.parse_args()

    return (options, args)

def main():

    (options, args) = main_options()

    mooltipass = MooltipassClient()

    # Ping the mooltipass, an integral part of the initialization process.
    if not mooltipass.ping():
        logging.error('Mooltipass did not reply to a ping request!')
        print('failure')
        sys.exit(0)

    # Ensure Mooltipass status
    quiet_bool = False
    while True:
        status = mooltipass.get_status()
        if status == 5:
            break
        logging.debug('Status != 5... it is: {0}'.format(status))
        if not quiet_bool:
            print('Insert a card and unlock the Mooltipass...')
        quiet_bool = True
        time.sleep(2)
    quiet_bool = False

    while not mooltipass.set_context(args[0]):
        mooltipass.add_context(args[0])

    mooltipass.set_login(options.login)
    mooltipass.set_password(options.password)

if __name__ == '__main__':

    main()

    # TODO:
    #   * Canceling request to add context loops and can't be terminated.
    #   * --password= is an awful argument, passwords should be randomly
    #     generated, obtained via raw_input() or warned against if provided
    #     by a --password argument (and warning supressed via --quiet if
    #     absolutely wanted).
    #   * Call .check_password() before setting password to avoid superfluous
    #     prompting of the user.
    #   * Add way of requesting username/password from context -- design for
    #     batch scripting.

