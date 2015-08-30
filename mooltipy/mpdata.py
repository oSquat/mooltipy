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

"""Importing & extracting files to and from the Mooltipass."""

from array import array
import logging
from optparse import OptionParser
import time
import sys

from mooltipy import MooltipassClient


def main_options():
    """Handles command-line interface, arguments & options."""

    usage = 'Usage: %prog {IMPORT|EXPORT} CONTEXT FILEPATH\n' + \
            'Example: %prog import ssh_key ~/.ssh/id_rsa'

    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    if not len(args) == 3:
        parser.error('Incorrect number of arguments; see --help.')
        sys.exit(0)

    if not args[0].lower() in ['import', 'export']:
        parser.error('Action must be import or export; see --help.')
        sys.exit(0)

    return (options, args)

def main():

    logging.basicConfig(
            format='%(levelname)s\t %(funcName)s():\t %(message)s',
            level=logging.DEBUG)

    (options, args) = main_options()

    action = args[0]
    context = args[1]
    filepath = args[2]

    mooltipass = MooltipassClient()

    if mooltipass is None:
        print('Mooltipass is None, this is a problem.')
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
        time.sleep(1)

    # Handle context
    while True:
        if mooltipass.set_data_context(context):
            logging.debug('Set context ' + context)
            break
        else:
            if action == 'export':
                print("Context does not exist; can't export.")
                sys.exit(0)
            if not mooltipass.add_data_context(context):
                print('User decliend to add context.')
                sys.exit(0)
            logging.debug('Context added')
            time.sleep(1)

    if action == 'import':
        with open(filepath, 'rb') as fin:
            data = array('B',fin.read())
        mooltipass.write_data_context(data)
    else:
        data = mooltipass.read_data_context()
        with open(filepath, 'wb') as fout:
            data.tofile(fout)

if __name__ == '__main__':

    main()

    # TODO: Pretty important
    #   * Alias argument "extract" as alternative to "export" because annoying
    #       also "upload" & "download"
    #   * Replace optparse with argparse
    #   * Python3 compatibility
    # TODO: Eventually
    #   * Some indication of progress -- transfer can be slow.
    #   * List data contexts
    #   * Delete data contexts
    #   * Warn on large files liable to induce sleep
