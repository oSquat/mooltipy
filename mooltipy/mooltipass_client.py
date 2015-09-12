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

from array import array
import random
import struct
import logging

from .mooltipass import _Mooltipass

# Delete me after removing read_all_nodes
from collections import defaultdict

class MooltipassClient(_Mooltipass):
    """Inherits _Mooltipass() and extends raw USB/firmware calls.

    Certain USB commands sent to the Mooltipass require some additional
    client-side code to be useful (e.g. ping; read/write data context)
    or there may not be a USB command at all (e.g. delete contexts).

    MooltipassClient is meant to be used by an application, extending
    the _Mooltipass class.
    """

    def __init__(self):
        super(MooltipassClient, self).__init__()
        if not self.ping():
            raise RuntimeError('Mooltipass did not respond to ping.')
        version_info = self.get_version()
        self.flash_size = version_info[2]
        self.version = version_info[3:].tostring()
        print('Connected to Mooltipass {} w/ {} Mb Flash'.format(self.version,
              self.flash_size))

    @property
    def status(self):
        return super(MooltipassClient, self).get_status()

    def ping(self):
        """Ping the mooltipass.

        Return true/false on success/failure.
        """
        try:
            data = array('B')
            data.append(random.randint(0,255))
            data.append(random.randint(0,255))
            data.append(random.randint(0,255))
            data.append(random.randint(0,255))

            super(MooltipassClient, self).ping(data)

            recv = None
            while recv is None or \
                    recv[self._DATA_INDEX] != data[0] or \
                    recv[self._DATA_INDEX+1] != data[1] or \
                    recv[self._DATA_INDEX+2] != data[2] or \
                    recv[self._DATA_INDEX+3] != data[3]:

                recv = super(MooltipassClient, self).recv_packet()

            logging.debug("Mooltipass replied to our ping message")
            return True

        except Exception as e:
            logging.error(e)
            return False

    def set_context(self, context):
        """Set mooltipass context.

        Return True if successful, False if context is unknown and
        None if no card is in the mooltipass.
        """
        resp = {0:False, 1:True, 3:None}
        return resp[super(MooltipassClient, self).set_context(context)]

    def set_password(self, password):
        """Set password for current context and login.

        Return 1 or 0 indicating success or failure.
        """
        if super(MooltipassClient, self).check_password(password):
            return 0
        else:
            return super(MooltipassClient, self).set_password(password)

    def start_memory_management(self, timeout=20000):
        """Enter memory management mode.

        Keyword argument:
            timeout -- how long to wait for user to complete entering pin 
                    (default 20000).

        Return true/false on success/failure. May raise RuntimeError
        if mooltipass is not unlocked.
        """

        # Memory management mode can only be accessed if the unit is unlocked.
        if not self.status == 0x05:
            raise RuntimeError('Cannot enter memory management mode; ' + \
                    'mooltipass not unlocked.')

        return super(MooltipassClient, self).start_memory_management(timeout)

    def write_data_context(self, data):
        """Write to mooltipass data context.

        Adds a layer to data which is necessary to enable retrieval.

        Arguments:
            data -- iterable data to save in context

        Return true/false on success/error.
        """

        # Prefix a length indicator to the start of our data. Reading
        # back from the mooltipass provides 32 byte blocks and the unit
        # has no concept of where in the final block our last byte is
        # located. Use this lenth indicator to find the end byte.
        lod = struct.pack('>L', len(data))
        ext_data = array('B', lod)
        ext_data.extend(data)

        return super(MooltipassClient, self).write_data_context(ext_data)

    def read_data_context(self):
        """Read data from context. Return data as array or None."""
        data = super(MooltipassClient, self).read_data_context()
        # See write_data_context for explanation of lod
        lod = struct.unpack('>L', data[:4])[0]
        logging.debug('Expecting: ' + str(lod) + ' bytes...')
        # TODO: Should I raise an error or otherwise handle when
        #   length of data received is shorter than expected?
        return data[4:lod+4]

    def read_node(self, node_number):
        recv = super(MooltipassClient, self).read_node(node_number)
        # Use flags to figure out the node type
        flags = struct.unpack('<H', recv[0:2])[0]
        if flags & 0xC000 == 0x00:
            # This is a parent node
            prev_parent_addr, next_parent_addr, next_child_addr = \
                struct.unpack('<HHH', recv[2:8])
            recv = recv[8:66]
            service_name = struct.unpack('<{}s'.format(len(recv)), recv)[0].strip('\0')
            return ParentNode(
                node_number,
                flags,
                prev_parent_addr,
                next_parent_addr,
                next_child_addr,
                service_name)

        elif flags & 0xC000 == 0x4000:
            # This is a credential child node
            prev_child_addr, next_child_addr, descr, date_created, date_last_used, ctr1, ctr2, ctr3, login, password = struct.unpack("<HH24sHH3b63s32s", recv[2:132])
            ctr = (ctr1 << 16) + (ctr2 << 8) + ctr3
            return ChildNode(node_number, flags, prev_child_addr, next_child_addr, descr[0], date_created, date_last_used, ctr, login, password)
        elif flags & 0xC000 == 0x8000:
            # This is the start of a data sequence
            print("Data nodes are not yet supported!")
        else:
            print("Unknown node type received!")

    def read_all_nodes(self):
        node_list = defaultdict(list)
        parent_address = self.get_starting_parent_address()
        while True:
            parent_node = self.read_node(parent_address)
            if parent_node.next_child_addr == 0:
                logging.info("Skipping {} with no children"\
                             .format(parent_node.service_name))
            else:
                child_node = self.read_node(parent_node.next_child_addr)
                node_list[parent_node.service_name].append(child_node)
                while child_node.next_child_addr != 0:
                    child_node = self.read_node(child_node.next_child_addr)
                    node_list[parent_node.service_name].append(child_node)
            parent_address = parent_node.next_parent_addr
            if parent_address == 0:
                break
        return node_list

    def parent_nodes(self):
        return _ParentNodes(self)

class ParentNode(object):
    """Represent node."""
    def __init__(
            self,
            node_addr,
            flags,
            prev_parent_addr,
            next_parent_addr,
            next_child_addr,
            service_name):

        self.node_addr = node_addr
        self.prev_parent_addr = prev_parent_addr
        self.next_parent_addr = next_parent_addr
        self.next_child_addr = next_child_addr
        self.service_name = service_name

    def __str__(self):
        return "<{}: Address:0x{:x}, PrevParent:0x{:x}, NextParent:0x{:x}, NextChild:0x{:x}, ServiceName:{}>".format(self.__class__.__name__, self.node_addr, self.prev_parent_addr, self.next_parent_addr, self.next_child_addr, self.service_name)

    def __repr__(self):
        return str(self)

class ChildNode(object):
    def __init__(
            self,
            node_addr,
            flags,
            prev_child_addr,
            next_child_addr,
            description,
            date_created,
            date_last_used,
            ctr,
            login,
            password):
        self.node_addr = node_addr
        self.flags = flags
        self.prev_child_addr = prev_child_addr
        self.next_child_addr = next_child_addr
        self.description = description
        self.date_created = date_created
        self.date_last_used = date_last_used
        self.ctr = ctr
        self.login = login
        self.password = password

    def __str__(self):
        return "<{}: Address:0x{:x} PrevChild:0x{:x} NextChild:0x{:x} Login:{}>".format(self.__class__.__name__, self.node_addr, self.prev_child_addr, self.next_child_addr, self.login)

    def __repr__(self):
        return str(self)

class _ParentNodes(object):
    """Parent node iterator.

    Intended to be returned to the user by way of method from
    MooltipassClient.
    """

    current_node = None
    next_parent_addr = None

    def __init__(self, parent_object):
        self._pobj = parent_object
        self.next_parent_addr = self._pobj.get_starting_parent_address()

    def __iter__(self):
        return self

    def next(self):
        #Python 2 compatibility
        return self.__next__()

    def __next__(self):
        if self.next_parent_addr == 0:
            raise StopIteration()

        self.current_node = self._pobj.read_node(self.next_parent_addr)
        self.next_parent_addr = self.current_node.next_parent_addr
        return self.current_node


class _ChildNodes(object):
    pass
