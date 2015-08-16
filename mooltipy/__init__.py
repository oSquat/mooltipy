"""Mooltipy - a python library for the Mooltipass

Mostly ripped out of mooltipas_coms.py from the mooltipass project (relative
path /tools/python_comms/mooltipass_coms.py). This is my learning guide with
a goal of creating a non-browser mooltipas management utility.

If you are having difficulty with core stuff (e.g. establishing a connection
to the mooltipass) it may be wise to compare with that file as I have trimmed
things down for simplicity.

Classes:
    Mooltipass -- Encapsulates access to a Mooltipass on your system

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


class Mooltipass(object):
    """"""

    _CMD_INDEX = 0x01
    _DATA_INDEX = 0x02

    _epin = None
    _epout = None
    _hid_device = None

    _intf = None

    def __init__(self):
        """Create object representing a Mooltipass.

        Raises RuntimeError on failure.
        """

        USB_VID = 0x16D0
        USB_PID = 0x09A0

        # Find the device
        self._hid_device = usb.core.find(idVendor=USB_VID, idProduct=USB_PID)

        if self._hid_device is None:
            raise RuntimeError('Mooltipass not found')

        # Different init codes depending on the platform
        if platform.system() == "Linux":
            try:
                self._hid_device.detach_kernel_driver(0)
                self._hid_device.reset()
            except Exception, e:
                pass # Probably already detached
        else:
            # Set the active configuration. With no arguments, the first configuration will be the active one
            try:
                self._hid_device.set_configuration()
            except Exception, e:
                raise RuntimeError('Cannot set device configuration: ' + str(e))

        # Get an endpoint instance
        cfg = self._hid_device.get_active_configuration()
        self._intf = cfg[(0,0)]

        # Match the first OUT endpoint
        self._epout = usb.util.find_descriptor(
                self._intf,
                custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        if self._epout is None:
            self._hid_device.reset()
            raise RuntimeError("Couldn't match the first OUT endpoint?")

        # Match the first IN endpoint
        self._epin = usb.util.find_descriptor(
                self._intf,
                custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        if self._epin is None:
            self._hid_device.reset()
            raise RuntimeError("Couldn't match the first IN endpoint?")

    @staticmethod
    def _tf_return(recv):
        """Return True or False based on typical command response."""
        DATA_INDEX = 2
        return (lambda recv: False if recv[DATA_INDEX] == 0 else True)(recv)

    def send_packet(self, cmd=0x00, data=None):
        """Sends a packet to our mooltipass.

        Keyword arguments:
            cmd -- command to send
            data -- array [or struct?]
        """

        data_len = 0
        if data is not None:
            data_len = len(data)

        # Data sent over to the generic HID should be in 64 byte packets and in
        # the following array structure:
        #   buffer[0]  = length of data
        #   buffer[1]  = command identifier for this packet
        #   buffer[2:] = packet data
        arraytosend = array('B')
        if cmd > 0x00:
            arraytosend.append(data_len)
            arraytosend.append(cmd)

        if data is not None:
            arraytosend.extend(data)

        self._epout.write(arraytosend)

    def recv_packet(self, timeout=5000):
        """Receives a packet from the mooltipass.

        Keyword arguments:
            timeout -- how long to wait for user to complete entering pin
                    (default 20000).
        """
        recv = None
        # The mooltipass should reply with 0xB9 if the user is currently
        # entering hs PIN, but I don't see this behavior
        while True:
            recv = self._epin.read(self._epin.wMaxPacketSize, timeout=timeout)
            if recv is not None and recv[self._DATA_INDEX] != 0xB9:
                break
            print(recv)
            time.sleep(.5)
        return recv

    def ping(self):
        """Ping the mooltipass (0xA1)

        Ping the mooltipass and return true/false on success/failure.
        """
        try:
            send_data = array('B')
            send_data.append(random.randint(0,255))
            send_data.append(random.randint(0,255))

            self.send_packet(CMD_PING, send_data)

            recv = None
            while recv is None or \
                    recv[self._DATA_INDEX] != send_data[0] or \
                    recv[self._DATA_INDEX+1] != send_data[1]:

                recv = self.recv_packet()

            logging.info("Mooltipass replied to our ping message")
            return True

        except usb.core.USBError as e:
            logging.error(e)
            return False

    def get_version(self):
        """Get mooltipass firmware version. (0xA2)"""
        #TODO: Figure out how to read the string version number?
        self.send_packet(CMD_VERSION, None)
        return self.recv_packet()

    def set_context(self, context):
        """Set mooltipass context. (0xA3)

        Returns True if successful, False if context is unknown and
        None if no card is in the mooltipass.
        """

        self.send_packet(CMD_CONTEXT, array('B', context + b'\x00'))
        recv = self.recv_packet(10000)
        if recv[self._DATA_INDEX] == 0:
            return False
        if recv[self._DATA_INDEX] == 1:
            return True
        if recv[self._DATA_INDEX] == 3:
            return None

    def get_login(self):
        """Get the login for current context. (0xA4)"""
        logging.info('Not yet implemented')
        pass

    def get_password(self):
        """Get the password for current context. (0xA5)"""
        logging.info('Not yet implemented')
        pass

    def set_login(self, login):
        """Set a login. (0xA6)"""
        self.send_packet(CMD_SET_LOGIN, array('B', login + b'\x00'))
        return self._tf_return(self.recv_packet())

    def set_password(self, password):
        """Set a password for current context. (0xA7)"""
        self.send_packet(CMD_SET_PASSWORD, array('B', password + b'\x00'))
        return self._tf_return(self.recv_packet())

    def check_password(self, password):
        """Compare given password to set password for context. (0xA8)

        Call check_password() to avoid calling set_password() and 
        prompting the user to overwrite a value that already exists.
        """
        logging.info('Not yet implemented')
        pass

    def add_context(self, context):
        """Add a context. (0xA9)"""
        self.send_packet(CMD_ADD_CONTEXT, array('B', context + b'\x00'))
        return self._tf_return(self.recv_packet())
    # TODO: Is there any way to delete contexts?

    def set_bootloader_password(self, password):
        """??? (0xAA)"""
        logging.info('Not yet implemented')
        pass

    def jump_to_bootloader(self):
        """??? (0xAB)"""
        logging.info('Not yet implemented')
        pass

    def get_random_number(self):
        """Get 32 random bytes. (0xAC)"""
        # TODO: Is this intended to be directly used in generation of
        #   a random password, or as seed in external PRNG?
        logging.info('Not yet implemented')
        pass

    def start_memory_management(self, timeout=20000):
        """Enter memory management mode. (0xAD)

        Keyword argument:
            timeout -- how long to wait for user to complete entering pin 
                    (default 20000).

            Note: Mooltipass times out after ~17.5 seconds of inaction
                    inaction.
        """

        # Memory management mode can only be accessed if the unit is unlocked.
        if not self.get_status() == 0x05:
            raise RuntimeError('Cannot enter memory management mode; ' + \
                    'mooltipass not unlocked.')

        self.send_packet(CMD_START_MEMORYMGMT, None)
        return self._tf_return(self.recv_packet())

    def start_media_import(self):
        """Request send media to Mooltipass. (0xAE)

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    def media_import(self, data):
        """Send data to mooltipass. (0xAF)

        Send specially formatted data to the mooltipass as part of a
        media import. <DOCUMENT FORMAT HERE IF POSSIBLE>

        Returns true/false on success/failure.
        """
        #TODO: Ask for pointer to source containing formatting!
        logging.info('Not yet implemented')
        pass

    def end_media_import(self):
        """Request end media to Mooltipass. (0xB0)

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    def set_mooltipass_parameter(self, param_id, value):
        """Set a mooltipass parameter. (0xB1)

        Arguments:
            param_id - Parameter ID to set
            value - Value to set

        Returns true/false on success/failure.
        """
        # TODO: Where are paremeters documented?
        logging.info('Not yet implemented')
        pass

    def get_mooltipass_parameter(self, param_id):
        """Retrieve a mooltipass parameter (0xB2).

        Arguments:
            param_id -- Parameter ID to get

        Returns the parameter value.
        """
        logging.info('Not yet implemented')
        pass

    def reset_card(self):
        """Reset inserted card. (0xB3)

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    def read_card_login(self):
        """Read login stored inside smartcard. (0xB4)

        Returns login or None.
        """
        logging.info('Not yet implemented')
        pass

    def read_card_password(self):
        """Read password stored inside the smartcard. (0xB5)

        Mooltipass asks for confirmation.

        Returns password or None.
        """
        logging.info('Not yet implemented')
        pass

    def set_card_login(self, login):
        """Set card login stored inside smartcard. (0xB6)

        Mooltipass asks for confirmation.

        Arguments:
            login -- Login value up to 62 bytes

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    def set_card_password(self, password):
        """Set password stored inside the smartcard. (0xB7)

        Mooltipass asks for confirmation.

        Arguments:
            password -- Password value up to 30 bytes.

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    def add_unknown_smartcard(self, cpz, ctr):
        """Instruct mooltipass to store an unknown smartcard. (0xB8)

        Arguments:
            ??? Not sure, experiment and review python_comms

        Returns true/false on success/failure.
        """
        logging.info('Not yet implemented')
        pass

    # TODO: Make a status property and this function private
    def get_status(self):
        """Return raw mooltipass status as int. (0xB9)

        The mooltipass returns a 1 byte bit field:
            Bit 0 -- Card presence
            Bit 1 -- Pin unlocking
            Bit 2 -- Card present and unlocked
            Bit 3 -- Unknown smart card inserted
        """
        # TODO: Interpret all bits; see /source_code/src/USB
        self.send_packet(CMD_MOOLTIPASS_STATUS, None)
        return self.recv_packet()[self._DATA_INDEX]

    # Where is 0xBA?

    def set_date(self):
        """Set current date. (0xBB)"""
        loggin.info('Not yet implemented')
        pass

    def set_mooltipass_uid(self):
        """Set the mooltipass UID. (0xBC)"""
        loggin.info('Not yet implemented')
        pass

    def get_mooltipass_uid(self):
        """Get the mooltipass UID. (0xBD)"""
        loggin.info('Not yet implemented')
        pass

    def set_data_context(self, context):
        """Set the data context. (0xBE)"""
        self.send_packet(CMD_SET_DATA_SERVICE, array('B', context + '\x00'))
        return self._tf_return(self.recv_packet())

    def add_data_context(self, context):
        """Add a data context. (0xBF)

        Arguments:
            context -- Name of context to add.

        Returns true/false on success/failure.
        """
        self.send_packet(CMD_ADD_DATA_SERVICE, array('B', context + '\x00'))
        return self._tf_return(self.recv_packet())

    def write_data_context(self, data):
        """Write to data context in blocks of 32 bytes. (0xC0)

        Data is sent to the mooltipass in 32 byte blocks. The the first
        byte of data sent with this command is an End of Data (EOD)
        marker. A non-zero value markes the data as the last block in
        sequence.

        After this EOD marker is 32 bytes of data making the total
        length of our transmission 33 bytes in size.

        Arguments:
            data -- iterable data to save in context

        Returns true/false on success/error.
        """

        BLOCK_SIZE = 32

        # Reading data back from the mooltipass also provides 32 byte
        # blocks. The last byte of our data falls somewhere within the
        # last 32 byte block. Add the length of expected data to the
        # the start of what we save to the mooltipass to fix this.
        lod = struct.pack('>H', len(data))
        ext_data = array('B', lod)
        ext_data.extend(data)

        for i in range(0,len(ext_data),BLOCK_SIZE):
            eod = (lambda byte: 0 if (len(ext_data) - byte > BLOCK_SIZE) else 1)(i)
            packet = array('B')
            packet.append(eod)
            packet.extend(ext_data[i:i+BLOCK_SIZE])
            self.send_packet(CMD_WRITE_32B_IN_DN, packet)
            if eod == 0 and not self._tf_return(self.recv_packet()):
                raise RuntimeError('Unexpected return')

        return True

    def read_data_context(self):
        """Read data from context in blocks of 32 bytes. (0xC1)

        Get successive 32 byte blocks of data until EOD.

        Returns data or None on error.
        """
        data = array('B')

        while True:
            self.send_packet(CMD_READ_32B_IN_DN, None)
            recv = self.recv_packet()
            print('Received ' + str(len(recv)) + ' of data -- raw dump:')
            #print(recv[self._DATA_INDEX:])
            if recv[0] == 0x01:
                break
            data += recv[self._DATA_INDEX:]
            #print(data)
            #print(recv)

        print(data)
            # TODO: Not receiving full data write if it exceeds 32 bytes.


    # TODO: Lots of commands...

    def end_memory_management(self):
        """End memory management mode. (0xD3)"""
        self.send_packet(CMD_END_MEMORYMGMT, None)
        return self._tf_return(self.recv_packet())

