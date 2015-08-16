"""Mooltipy - a python library for the Mooltipass.

Classes:
    Mooltipass -- Encapsulate access to Mooltipass's USB commands. This
                class is designed to be inherited (particularly by
                MooltipassClient()) and represents the server half of
                of the Client-Server / App-Mooltiplass relationship.
    MooltipassClient -- Act as an abstraction layer between the
                Mooltipass and an application. The majority of exposed
                methods and attributes should come from this class
                where any post-command-response-processing is handled.

"""

from array import array

import logging
import platform
import random
import struct
import sys
import time

import usb.core

from .constants import *
from .mooltipass import _Mooltipass


class MooltipassClient(_Mooltipass):
    """Inherits _Mooltipass() and extends native firmware calls."""

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

            logging.info("Mooltipass replied to our ping message")
            return True

        except usb.core.USBError as e:
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
