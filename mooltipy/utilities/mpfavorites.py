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
import sys
import logging
import time

from mooltipy.mooltipass_client import MooltipassClient

try:
    input = raw_input
except NameError:
    # For python 2/3 compatibility
    pass

def list_favorites(mooltipass, args):
    favorites = []
    for slot in range(0, 14):
        fav_slot_info = mooltipass.get_favorite(slot)
        if fav_slot_info[0] != 0:
            favorites.append((slot, fav_slot_info))
    if not len(favorites):
        print("No favorites configured!")
    else:
        for favorite in favorites:
            context_info = mooltipass.read_node(favorite[1][0])
            child_info = mooltipass.read_node(favorite[1][1])
            print("Favorite Slot {} - {}:{}".format(favorite[0],
                                                    context_info.service_name,
                                                    child_info.login))

def get_favorite(mooltipass, args):
    """Gets the favorite information from the specified slot"""
    # Argparse takes care of validation for us
    fav_slot_info = mooltipass.get_favorite(args.favorite_slot)
    if fav_slot_info[0] == 0:
        print("No favorite stored in slot {}".format(args.favorite_slot))
        return
    context_info = mooltipass.read_node(fav_slot_info[0])
    child_info = mooltipass.read_node(fav_slot_info[1])
    print("Context: {}".format(context_info.service_name))
    print("  Login: {}".format(child_info.login))

def set_favorite(mooltipass, args):
    """Sets a context into a favorite slot"""
    ctx_favorite_list = []
    for pnode in mooltipass.parent_nodes('login'):
        for cnode in pnode.child_nodes():
            ctx_favorite_list.append((pnode, cnode))

    for index, ctx in enumerate(ctx_favorite_list):
        print('{} - {}:{}'.format(index, ctx[0].service_name, ctx[1].login))

    selected_favorite = 1000
    while selected_favorite > len(ctx_favorite_list):
        selected_favorite = int(input("Please select a context:"))

    favorite_slot = 1000
    while favorite_slot >= 14:
        favorite_slot = int(input("Please select a favorite slot(0-13):"))

    print('Putting {}:{} in favorite slot {}'.format(ctx_favorite_list[selected_favorite][0].service_name, ctx_favorite_list[selected_favorite][1].login, favorite_slot))
    print(ctx_favorite_list[selected_favorite][0].node_addr, ctx_favorite_list[selected_favorite][1].node_addr)
    logging.debug('Parent Addr:0x{:x} Child Addr:0x{:x}'.format(ctx_favorite_list[selected_favorite][0].node_addr, ctx_favorite_list[selected_favorite][1].node_addr))

    mooltipass.set_favorite(favorite_slot,
                            (ctx_favorite_list[selected_favorite][0].node_addr,
                             ctx_favorite_list[selected_favorite][1].node_addr))

def del_favorite(mooltipass, args):
    """Removes a favorite from the specified slot"""
    mooltipass.set_favorite(args.favorite_slot, (0, 0))

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

    parser.add_argument('-sme', '--skip_mgmt_enter', help='Skip entering management mode', action='store_true')
    parser.add_argument('-smx', '--skip_mgmt_exit', help='Skip exiting management mode', action='store_true')

    # subparser
    subparsers = parser.add_subparsers(
            dest = 'command', help='action to take on context')

    # get
    # ---
    get_parser = subparsers.add_parser(
            'get',
            help = 'Get a favorite or favorites',
            prog = cmd_util+' get')
    get_parser.add_argument("favorite_slot", help='specify context (e.g. Lycos.com)', choices=range(0,14), type=int)

    # set
    # ---
    set_parser = subparsers.add_parser(
            'set',
            help = 'Set or update a favorite',
            prog = cmd_util+' set')

    # delete
    # ------
    del_parser = subparsers.add_parser(
            'del',
            help='Delete a favorite',
            prog=cmd_util+' del')
    del_parser.add_argument("favorite_slot", type=int, help='specify context (e.g. Lycos.com)', choices=range(0,14))

    # list
    # ----
    list_parser = subparsers.add_parser(
            'list',
            help = 'List all favorites',
            prog = cmd_util+' list')

    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    return args

def main():

    command_handlers = {
        'get':get_favorite,
        'set':set_favorite,
        'del':del_favorite,
        'list':list_favorites
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

    if args.skip_mgmt_enter == False:
        mooltipass.start_memory_management()
    command_handlers[args.command](mooltipass, args)
    if args.skip_mgmt_exit == False:
        mooltipass.end_memory_management()

    sys.exit(0)

if __name__ == '__main__':

    main()
