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
