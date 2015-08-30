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

"""A command line utility for managing login contexts in the
mooltipass.
"""

from optparse import OptionParser
import time

from mooltipy import MooltipassClient

def main_options():
    """Handles command-line interface, arguments & options. """

    usage = 'Usage: %prog {context} [OPTIONS]\n' + \
            'Example: %prog Lycos.com --login=jsmith --password="not_random"'

    parser = OptionParser(usage)
    parser.add_option('--login', dest='login', metavar='USER',
            help='login for context')
    parser.add_option('--password', dest='password', metavar='PASS',
            help='password for login')

    (options, args) = parser.parse_args()

    if not len(args) == 1:
        parser.error('Incorrect number of arguments; see --help.')

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

    #TODO: theres a lot left to be desired here

