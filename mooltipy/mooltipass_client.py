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

PARENT_NODE = 0x0000
CHILD_NODE = 0x4000
PARENT_DATA = 0x8000
CHILD_DATA = 0xC000


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

        # Already in memory management mode if we can get starting parent
        if super(MooltipassClient, self).get_starting_parent_address():
            return True

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

    def read_node(self, node_addr, parent_weak_ref=None):
        """Extend Mooltipass class to return a Node object.

        Arguments:
            node_addr       -- Address of node to fetch.
            parent_weak_ref -- Specifies the return object's parent.
                This allow child nodes to refer to their parent's
                functions & variables. Optional, and default assumes
                the parent object is Mooltipassclient.
        """
        recv = super(MooltipassClient, self).read_node(node_addr)
        if parent_weak_ref == None:
            parent_weak_ref = weakref.ref(self)()
        # Use flags to figure out the node type
        flags = struct.unpack('<H', recv[:2])[0]
        if flags & 0xC000 == PARENT_NODE:
            # This is a parent node
            return ParentNode(node_addr, recv, parent_weak_ref)
        elif flags & 0xC000 == CHILD_NODE:
            # This is a credential child node
            return ChildNode(node_addr, recv, parent_weak_ref)
        elif flags & 0xC000 == PARENT_DATA:
            return ParentNode(node_addr, recv, parent_weak_ref)
        else:
            return DataNode(node_addr, recv, parent_weak_ref)

    def write_node(self, node):
        """Write to a node in memory."""
        return super(MooltipassClient, self)._write_node(node.addr, node.raw)

    def parent_nodes(self, node_type=None):
        """Return a ParentNodes iter.

        Arguments:
            node_type = [login|data]
        """
        # TODO: Comment and make a property too?
        return _ParentNodes(node_type, self)

    def set_starting_parent(self, parent_addr):
        """Set the starting parent node.

        Overrides mooltipass._set_starting_parent() and add some protection
        to the call by ensuring the address specified is valid.
        """
        valid_addresses = [0]
        for pnode in self.parent_nodes('login'):
            valid_addresses.append(pnode.addr)

        # You can brick your mooltipass by providing an invalid starting parent.
        if not parent_addr in valid_addresses:
            raise RuntimeError('Can not set the starting parent to an invalid node address!')

        return super(MooltipassClient, self)._set_starting_parent(parent_addr)

    def set_starting_data_parent_addr(self, parent_addr):
        """Set the starting parent node.

        Overrides mooltipass._set_starting_data_parent_addr() and add some
        protection to the call by ensuring the address specified is valid.
        """
        valid_addresses = [0]
        for pnode in self.parent_nodes('data'):
            valid_addresses.append(pnode.addr)

        if not parent_addr in valid_addresses:
            raise RuntimeError('Can not set the starting parent to an invalid node address!')

        return super(MooltipassClient, self)._set_starting_data_parent_addr(parent_addr)


class Node(object):
    """Parent/Child/Data nodes have some similar, overlapping structure.

    The Node class is intended to be inherited by Parent/Child/DataNode classes.
    """
    # Node should accept a raw array of data from read_node(). Access to
    # each element contained within a node should be controlled through
    # properties. This is not a typical design in Python, but in our case
    # manipulation of nodes should be minimal (so performance is not a
    # concern), separate properties will help clearly delineate values
    # from the contiguous array of bytes provided by read_node(), and
    # properties will be necessary for bound checking to aide in adhering
    # to the constraints of the Mooltipass's node structure.

    addr = None
    raw = None
    _parent = None

    @property
    def flags(self):
        return struct.unpack('<H', self.raw[:2])[0]

    @property
    def first_addr(self):
        # The 2 bytes after flags is always an address but its use
        # differs by node type:
        #  * ParentNode.prev_parent_addr
        #  * ChildNode.prev_child_addr
        #  * DataNode.next_data_addr
        return struct.unpack('<H', self.raw[2:4])[0]

    @first_addr.setter
    def first_addr(self, value):
        self.raw[2:4] = array('B', struct.pack('<H', value))

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

    @property
    def prev_parent_addr(self):
        return super(ParentNode, self).first_addr

    @prev_parent_addr.setter
    def prev_parent_addr(self, value):
        super(ParentNode, ParentNode).first_addr.__set__(self, value)

    @property
    def next_parent_addr(self):
        return struct.unpack('<H', self.raw[4:6])[0]

    @next_parent_addr.setter
    def next_parent_addr(self, value):
        self.raw[4:6] = array('B', struct.pack('<H', value))

    @property
    def next_child_addr(self):
        return struct.unpack('<H', self.raw[6:8])[0]

    @next_child_addr.setter
    def next_child_addr(self, value):
        self.raw[6:8] = array('B', struct.pack('<H', value))

    @property
    def service_name(self):
        return struct.unpack('<58s', self.raw[8:66])[0].strip(b'\0')

    def __str__(self):
        return "<{}: Address:0x{:x}, PrevParent:0x{:x}, NextParent:0x{:x}, NextChild:0x{:x}, ServiceName:{}>".format(self.__class__.__name__, self.node_addr, self.prev_parent_addr, self.next_parent_addr, self.next_child_addr, self.service_name)

    def __repr__(self):
        return str(self)

    def write(self):
        return self._parent._write_node(self.addr, self.raw)

    def delete(self):
        """Delete a parent node."""

        # Delete all children belonging to our node
        for cnode in self.child_nodes():
            cnode.delete()

        if self.prev_parent_addr == 0:
            # If deleting the first node in our linked list
            if self.flags & 0xC000 == PARENT_NODE:
                self._parent.set_starting_parent(self.next_parent_addr)
            elif self.flags & 0xC000 == PARENT_DATA:
                self._parent.set_starting_data_parent_addr(self.next_parent_addr)
        else:
            prev_node = self._parent.read_node(self.prev_parent_addr)
            prev_node.next_parent_addr = self.next_parent_addr
            prev_node.write()

        if self.next_parent_addr > 0:
            # If this is not the last node in our linked list
            next_node = self._parent.read_node(self.next_parent_addr)
            next_node.prev_parent_addr = self.prev_parent_addr
            next_node.write()

        # Fill node; zero addresses
        self.raw = array('B', '\xff'*132)
        self.prev_parent_node = 0
        self.next_parent_node = 0
        self.write()

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

    @property
    def prev_child_addr(self):
        return super(ChildNode, self).first_addr

    @prev_child_addr.setter
    def prev_child_addr(self, value):
        super(ChildNode, ChildNode).first_addr.__set__(self, value)

    @property
    def next_child_addr(self):
        return struct.unpack('<H', self.raw[4:6])[0]

    @next_child_addr.setter
    def next_child_addr(self, value):
        self.raw[4:6] = array('B', struct.pack('<H', value))

    @property
    def description(self):
        return struct.unpack('<24s', self.raw[6:30])[0].strip('\0')

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
        return struct.unpack('<63s', self.raw[37:100])[0].strip(b'\0')

    @login.setter
    def login(self, value):
        if len(value) > 62:
            raise RuntimeError('Login can not exceed 62 characters.')
        value += ('\x00' * (len(value) - 63))
        self.raw[37:100] = array('B', struct.pack('<63s', value))
        pass

    @property
    def password(self):
        return struct.unpack('<32s', self.raw[100:132])[0]

    def __str__(self):
        return "<{}: Address:0x{:x} PrevChild:0x{:x} NextChild:0x{:x} Login:{}>".format(self.__class__.__name__, self.node_addr, self.prev_child_addr, self.next_child_addr, self.login)

    def __repr__(self):
        return str(self)

    def write(self):
        return self._parent._parent._write_node(self.addr, self.raw)

    def delete(self):
        """Delete a child node."""
        if self.prev_child_addr == 0:
            # If there is a previous_child_node under this parent, update it
            # so it points to the next valid node
            self._parent.next_child_addr = self.next_child_addr
            self._parent.write()
        else:
            # If no prev_child_addr exists, update the parent node instead
            prev_child_node = self._parent._parent.read_node(self.prev_child_addr, self._parent)
            prev_child_node.next_child_addr = self.next_child_addr
            prev_child_node.write()

        # If there is a next_child_node, its prev_child_addr must be updated
        if self.next_child_addr != 0:
            next_child_node = self._parent._parent.read_node(self.next_child_addr, self._parent)
            next_child_node.prev_child_addr = self.prev_child_addr
            next_child_node.write()

        # Fill the node so it is not considered an oprhan
        self.raw = array('B', '\xff'*132)
        self.write()


class DataNode(Node):
    """Represent a data [child] node.

    Inherits Node.
    """

    @property
    def flags(self):
        return super(DataNode, self).flags

    @property
    def next_data_addr(self):
        return super(DataNode, self).first_addr

    @property
    def data(self):
        return struct.unpack('<128s', self.raw[4:132])[0]

    def write(self):
        return self._parent._parent._write_node(self.addr, self.raw)

    def delete(self):
        """Delete this data node."""
        # With ordinary nodes you need to update the starting address if the
        # first child node is deleted. With data, the only time we'd be deleting
        # child nodes is when we're deleting all child nodes so I don't believe
        # this is necessary.

        # Fill the node so it is not considered an oprhan
        self.raw = array('B', '\xff'*132)
        self.write()


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
        # TODO: Allow None and iterate all nodes starting at 0; identify by flags.
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
        # Python 2 compatibility
        return self.__next__()

    def __next__(self):
        if self.next_parent_addr == 0:
            raise StopIteration()

        self.current_node = self._parent.read_node(self.next_parent_addr)
        self.next_parent_addr = self.current_node.next_parent_addr
        return self.current_node


class _ChildNodes(object):
    """Child [or Data] node iterator.

    Intended to be returned to the user by way of method from
    the ParentNode class: MooltipassClient.ParentNode.child_nodes().
    """
    # All storage nodes start with a parent. Some parents point to child nodes
    # and store credentials; some parents point to data nodes to store data.
    # Rather than a separate iter for child and data nodes, just this one
    # is fine. The only problem is a slight inconsistency in the property
    # containing the address of the next node in series explained below.

    current_node = None
    next_addr = None

    def __init__(self, parent):
        self._parent_ref = weakref.ref(parent)
        self._parent = self._parent_ref()
        self.next_addr = self._parent.next_child_addr

    def __iter__(self):
        return self

    def next(self):
        #Python 2 compatibility
        return self.__next__()

    def __next__(self):
        if self.next_addr == 0:
            raise StopIteration()

        # The Mooltipass node structure goes Mooltipass.ParentNode.ChildNode
        # and ._parent points up one level up therefore:
        # self._parent._parent.read_node() == \
        #       _ChildNodes.ParentNode.Mooltipass.read_node()
        self.current_node = self._parent._parent.read_node(self.next_addr, self._parent)

        # Child nodes store the next address in .next_child_addr while data
        # nodes use .next_data_addr
        if self._parent.flags & 0xC000 == PARENT_NODE:
            self.next_addr = self.current_node.next_child_addr
        elif self._parent.flags & 0xC000 == PARENT_DATA:
            self.next_addr = self.current_node.next_data_addr
        return self.current_node
