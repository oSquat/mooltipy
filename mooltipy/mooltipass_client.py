
from array import array
import random
import struct
import logging

from .mooltipass import _Mooltipass

class MooltipassClient(_Mooltipass):
    """Inherits _Mooltipass() and extends raw firmware calls.

    Certain USB commands sent to the Mooltipass require some additional
    client-side code to be useful (e.g. ping; read/write data context)
    or there may not be a USB command at all (e.g. delete contexts).

    MooltipassClient is meant to be used by an application, extend the
    _Mooltipass class.
    """

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
            #data.append(random.randint(0,255))
            #data.append(random.randint(0,255))

            super(MooltipassClient, self).ping(data)

            recv = None
            while recv is None or \
                    recv[self._DATA_INDEX] != data[0] or \
                    recv[self._DATA_INDEX+1] != data[1]:

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

        Arguments:
            data -- iterable data to save in context

        Return true/false on success/error.
        """

        # Reading data back from the mooltipass also provides 32 byte
        # blocks. The last byte of our data falls somewhere within the
        # last 32 byte block. Prefix the length of our data to the start
        # of the data we were given handle this problem.
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
        return data[4:lod+4]

    # TODO: Lots of commands...
