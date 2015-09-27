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
import weakref

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
        self.flash_size = version_info[0]
        self.version = version_info[1]
        logging.debug('Connected to Mooltipass {} w/ {} Mb Flash'.format(
                self.version,
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
                    recv[0] != data[0] or \
                    recv[1] != data[1] or \
                    recv[2] != data[2] or \
                    recv[3] != data[3]:

                recv, _ = super(MooltipassClient, self).recv_packet()

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

    def write_data_context(self, data, callback=None):
        """Write to mooltipass data context.

        Adds a layer to data which is necessary to enable retrieval.

        Arguments:
            data -- iterable data to save in context
            callback -- function to receive tuple containing progress
                    in tuple form (x, y) where x is bytes sent and y
                    is size of transmission.

        Return true/false on success/error.
        """

        # Prefix a length indicator to the start of our data. Reading
        # back from the mooltipass provides 32 byte blocks and the unit
        # has no concept of where in the final block our last byte is
        # located. Use this lenth indicator to find the end byte.
        lod = struct.pack('>L', len(data))
        ext_data = array('B', lod)
        ext_data.extend(data)

        return super(MooltipassClient, self).write_data_context(ext_data, callback)

    def read_data_context(self, callback=None):
        """Read data from context. 

        Arguments:
            callback    -- Callback function which must accept a tuple
                            containing (x, y) where x is the current
                            position and y is the full size expected.

        Return data as array or None.
        """

        data = super(MooltipassClient, self).read_data_context(callback)
        # See write_data_context for explanation of lod
        lod = struct.unpack('>L', data[:4])[0]
        logging.debug('Expecting: ' + str(lod) + ' bytes...')
        if not lod <= len(data):
            raise RuntimeError('The size of data received from the device ' + \
                    'does not match what was expected. This can happen if ' + \
                    'a data transfer was cancelled.')
        return data[4:lod+4]

    def read_node(self, node_addr):
        """Extend Mooltipass class to return a Node object."""
        PARENT_NODE = 0x0000
        CHILD_NODE = 0x4000
        DATA_NODE = 0x8000

        recv = super(MooltipassClient, self).read_node(node_addr)
        # Use flags to figure out the node type
        flags = struct.unpack('<H', recv[:2])[0]
        if flags & 0xC000 == PARENT_NODE:
            # This is a parent node
            return ParentNode(node_addr, recv, weakref.ref(self)())
        elif flags & 0xC000 == CHILD_NODE:
            # This is a credential child node
            return ChildNode(node_addr, recv, weakref.ref(self)())
        elif flags & 0xC000 == DATA_NODE:
            return ParentNode(node_addr, recv, weakref.ref(self)())
        else:
            raise RuntimeError("Unknown node type received!")

    def parent_nodes(self, node_type=None):
        """Return a ParentNodes iter."""
        # TODO: Comment and make a property too?
        return _ParentNodes(node_type, self)


class Node(object):
    """Parent/Child/Data nodes have some overlapping structure.

    Node is intended to be inherited by Parent/Child/DataNode classes.
    """
    # Nodes should accept a raw array of data from read_node(). Access to
    # each element contained within a node should be controlled through
    # properties. This is not a typical design in Python, but in our case
    # manipulation of nodes should be minimal (so performance is not a
    # concern), separate properties will help clearly delineate values
    # from the contiguous array of data, and properties will be necessary
    # for bound checking to aide in adhering to the constraints of the
    # Mooltipass's node structure.

    addr = None
    raw = None

    @property
    def flags(self):
        return struct.unpack('<H', self.raw[:2])[0]

    @flags.setter
    def flags(self, value):
        pass

    @property
    def first_addr(self):
        # The 2 bytes after flags is always an address but its use
        # differs by node type:
        #  * ParentNode.prev_parent_addr
        #  * ChildNode.next_child_addr
        #  * DataNode.next_addr
        return struct.unpack('<H', self.raw[2:4])[0]

    @first_addr.setter
    def first_addr(self, value):
        pass

    def __init__(self, node_addr, recv, parent_weak_ref = None):
        self.addr = node_addr
        self.raw = recv
        self._parent = parent_weak_ref


class ParentNode(Node):
    """Represent a parent node.

    Inherits Node.
    """

    @property
    def flags(self):
        return super(ParentNode, self).flags

    @flags.setter
    def flags(self, value):
        super(ParentNode, self).flags

    @property
    def prev_parent_addr(self):
        return super(ParentNode, self).first_addr

    @prev_parent_addr.setter
    def prev_parent_addr(self, value):
        super(ParentNode, self).first_addr

    @property
    def next_parent_addr(self):
        return struct.unpack('<H', self.raw[4:6])[0]

    @next_parent_addr.setter
    def next_parent_addr(self, value):
        pass

    @property
    def next_child_addr(self):
        return struct.unpack('<H', self.raw[6:8])[0]

    @next_child_addr.setter
    def next_child_addr(self, value):
        pass

    @property
    def service_name(self):
        return struct.unpack('<58s', self.raw[8:66])[0].strip('\0')

    @service_name.setter
    def service_name(self, value):
        pass

    def __str__(self):
        return "<{}: Address:0x{:x}, PrevParent:0x{:x}, NextParent:0x{:x}, NextChild:0x{:x}, ServiceName:{}>".format(self.__class__.__name__, self.node_addr, self.prev_parent_addr, self.next_parent_addr, self.next_child_addr, self.service_name)

    def __repr__(self):
        return str(self)

    def child_nodes(self):
        """Return a child node iter."""
        return _ChildNodes(self)


class ChildNode(Node):
    """Represent a child node.

    Inherits Node.
    """

    @property
    def flags(self):
        return super(ChildNode, self).flags

    @flags.setter
    def flags(self, value):
        super(ChildNode, self).flags

    @property
    def prev_child_addr(self):
        return super(ChildNode, self).first_addr

    @prev_child_addr.setter
    def prev_child_addr(self, value):
        super(ChildNode, self).first_addr

    @property
    def next_child_addr(self):
        return struct.unpack('<H', self.raw[4:6])[0]

    @next_child_addr.setter
    def next_child_addr(self, value):
        pass

    @property
    def description(self):
        return struct.unpack('<24s', self.raw[6:30])[0].strip('\0')

    @description.setter
    def description(self, value):
        pass

    @property
    def date_created(self):
        return struct.unpack('<H', self.raw[30:32])[0]

    @property
    def date_last_used(self):
        return struct.unpack('<H', self.raw[32:34])[0]

    @property
    def ctr(self):
        c1, c2, c3 = struct.unpack('<3b', self.raw[34:37])[0]
        # I have no idea if this is correct
        return (c1 << 16) + (c2 << 8) + c3

    @property
    def login(self):
        return struct.unpack('<63s', self.raw[37:100])[0]

    @login.setter
    def login(self, value):
        pass

    @property
    def password(self):
        return struct.unpack('<32s', self.raw[100:132])[0]


    def __str__(self):
        return "<{}: Address:0x{:x} PrevChild:0x{:x} NextChild:0x{:x} Login:{}>".format(self.__class__.__name__, self.node_addr, self.prev_child_addr, self.next_child_addr, self.login)

    def __repr__(self):
        return str(self)


class _ParentNodes(object):
    """Parent node iterator.

    Intended to be returned to the user by way of method from
    MooltipassClient: MooltipassClient.parent_nodes()
    """
    node_type = None
    current_node = None
    next_parent_addr = None

    def __init__(self, node_type=None, parent=None):
        """Instantiate a parent node iterator.

        Arguments:
            node_type = [login|data]
            parent = Reference to parent object (i.e. Mooltipass)
        """
        # TODO: Allow None and iterate all nodes starting at 0; identify type
        #   of node with self.node_type?
        if not node_type in ['login','data']:
            raise RuntimeError('node_type must be \'login\' or \'data\'')
        self._node_type = node_type
        self._parent_ref = weakref.ref(parent)
        self._parent = self._parent_ref()
        if node_type == 'login':
            self.next_parent_addr = self._parent.get_starting_parent_address()
        else:
            self.next_parent_addr = self._parent.get_starting_data_parent_address()

    def __iter__(self):
        return self

    def next(self):
        #Python 2 compatibility
        return self.__next__()

    def __next__(self):
        if self.next_parent_addr == 0:
            raise StopIteration()

        self.current_node = self._parent.read_node(self.next_parent_addr)
        self.next_parent_addr = self.current_node.next_parent_addr
        return self.current_node


class _ChildNodes(object):
    """Child node iterator.

    Intended to be returned to the user by way of method from
    the ParentNode class: pnode.child_nodes().
    """

    current_node = None
    next_child_addr = None

    def __init__(self, parent):
        self._parent_ref = weakref.ref(parent)
        self._parent = self._parent_ref()
        self.next_child_addr = self._parent.next_child_addr

    def __iter__(self):
        return self

    def next(self):
        #Python 2 compatibility
        return self.__next__()

    def __next__(self):
        if self.next_child_addr == 0:
            raise StopIteration()

        self.current_node = self._parent._parent.read_node(self.next_child_addr)
        self.next_child_addr = self.current_node.next_child_addr
        return self.current_node
