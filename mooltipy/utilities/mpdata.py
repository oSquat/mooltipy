#!/usr/bin/env python3
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

"""Import & export small files to and from the Mooltipass."""

import argparse
from array import array
import logging
import os
import time
import sys

from mooltipy.mooltipass_client import MooltipassClient


def main_options():
    """Handles command-line interface, arguments & options."""

    # If the wrapper was used to execute our utility instead of directly
    util = ''
    if os.path.split(sys.argv[0])[1] in ['./mooltipy.py', 'mooltipy']:
        # Get the utility name contained in argv[1]
        util = sys.argv[1]
        del sys.argv[1]

    # Create a string to represent the utility in help messages
    cmd_util = (' '.join([os.path.split(sys.argv[0])[1], util])).strip()

    description = 'Manages mooltipass data contexts.'.format(
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
            dest = 'command', help='action to take on context', required=True)

    # get
    # ---
    description = 'Retrieve data from a data context.'
    get_parser = subparsers.add_parser(
            'get',
            help = 'retrieve data for a given context',
            description = description,
            prog = cmd_util+' get')
    get_parser.add_argument('context', help='specify context')
    get_parser.add_argument('filepath',
            nargs = '?',
            default = None,
            help = 'file to which data should be written, if no file is '
                    ' specified data is written to stdout')

    # set
    # ---
    description = 'Create a new context to store data.\n\n' \
            'Examples:\n' \
            '\t# Create a data context called ssh_key and import key\n' \
            '\t$ {cmd_util} set ssh_key ~/.ssh/id_rsa\n\n' \
            '\t# Restore ssh_key to ./restored_key\n' \
            '\t$ {cmd_util} get ssh_key ./restored_key\n\n' \
            '\t# Read from / write to stdin / stdout\n' \
            '\t$ echo "this-is-a-secure-api-key" | {cmd_util} set example-api-key\n' \
            '\t$ echo $({cmd_util} get example-api-key)\n' \
            '\t  this-is-a-secure-api-key'
    set_parser = subparsers.add_parser(
            'set',
            help = 'create and import data into a data context',
            description = description.format(cmd_util = cmd_util),
            formatter_class = argparse.RawDescriptionHelpFormatter,
            prog = cmd_util+' set')
    set_parser.add_argument('context', help='specify context')
    set_parser.add_argument('filepath',
            nargs = '?',
            default = None,
            help = 'file from which data should be read')

    # delete
    # ------
    description = 'Delete a mooltipass data context.'
    del_parser = subparsers.add_parser(
            'del',
            help = 'delete a context',
            description = description,
            prog = cmd_util+' del')
    del_parser.add_argument("context", help='specify context')

    # list
    # ----
    description = 'List data contexts stored in the mooltipass.'
    list_parser = subparsers.add_parser(
            'list',
            help = 'list login contexts',
            description = description,
            prog = cmd_util + ' list')

    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    # end subparsers
    args = parser.parse_args()

    return args

def get_context(mooltipass, args):
    """Retrieve data from a data context."""
    if not mooltipass.set_data_context(args.context):
        raise RuntimeError('Context does not exist; cannot get context.')

    if args.filepath is None:
        data = mooltipass.read_data_context()
        for c in data:
            sys.stdout.write(chr(c))
        sys.stdout.flush()
    else:
        data = mooltipass.read_data_context(callback)
        with open(args.filepath, 'wb') as fout:
            data.tofile(fout)

def callback(progress):
    """Report progress of file transfer."""
    current = progress[0]
    full = progress[1]
    if current > full:
        current = full
    percent = float(current)*100 / full
    progbar = int(round(percent / 5,0))
    sys.stdout.write('\r[{0}] {1:>0.1f}%'.format(
            '#'*progbar + ' '*(20-progbar), percent))
    sys.stdout.flush()

def set_context(mooltipass, args):
    """Create and import data to a data context."""
    while not mooltipass.set_data_context(args.context):
        if not mooltipass.add_data_context(args.context):
            raise RuntimeError('Request to add context denied or timed out.')

    if args.filepath is None:
        data = array('B', sys.stdin.read())
    else:
        with open(args.filepath, 'rb') as fin:
            data = array('B',fin.read())

    mooltipass.write_data_context(data, callback)

def del_context(mooltipass, args):
    """Delete a data context."""

    if not mooltipass.set_data_context(args.context):
        raise RuntimeError('That context ({}) does not exist.'.format(args.context))

    mooltipass.start_memory_management()

    for pnode in mooltipass.parent_nodes('data'):
        if pnode.service_name == args.context:
            pnode.delete()

    if args.skip_mgmt_exit == False:
        mooltipass.end_memory_management()

def list_context(mooltipass, args):
    """Display a list of data contexts."""
    mooltipass.start_memory_management()
    s = '{:<40}{:<40}\n'.format('Context:','Approximate Size:')
    s += '{:<40}{:<40}\n'.format('--------','----------------')
    for pnode in mooltipass.parent_nodes('data'):
        service_name = pnode.service_name
        c = 0
        for cnode in pnode.child_nodes():
            c += 1
        s += '{:<40}{:<40}\n'.format(service_name, c*128)
    print(s)
    if args.skip_mgmt_exit == False:
        mooltipass.end_memory_management()

def main():

    logging.basicConfig(
            #format='%(levelname)s\t %(funcName)s():\t %(message)s',
            format='%(message)s',
            level=logging.INFO)
            #level=logging.DEBUG)

    command_handlers = {
        'get':get_context,
        'set':set_context,
        'del':del_context,
        'list':list_context
    }

    args = main_options()

    mooltipass = MooltipassClient()

    if mooltipass is None:
        print('Mooltipass is None, this is a problem.')
        sys.exit(0)

    try:
        # Ensure Mooltipass status
        if not mooltipass.get_status() == 5:
            print('Insert a card and unlock the Mooltipass or cancel with ctrl-c')
            while True:
                if mooltipass.get_status() == 5:
                    break
                time.sleep(1)

        command_handlers[args.command](mooltipass, args)
        sys.exit(0)
    except (KeyboardInterrupt, SystemExit):
        print('')
    except Exception as e:
        print('\nAn error occurred: \n{}'.format(e))
    finally:
        pass

if __name__ == '__main__':

    main()

    # TODO: Important
    #   * Unexpected return on import to existing context?
	# 	* Handle error on mpdata set if context exists
    # TODO: Soon
    #   * On import, referencing file that doesn't exist causes failure
    #   * Replace optparse with argparse
    #   * On export, warn before clobbering file?
    #   * Warn on large files liable to induce sleep
    # TODO: Eventually
    #   * Support reading from / writing to stdin / stdout
    #   * Some indication of progress -- transfer can be slow.
    #   * List data contexts
    #   * Delete data contexts
    #   * Alias argument "extract" as alternative to "export" because annoying
    #       also "upload" & "download"
