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

"""Contains the Mooltipass USB command side of our mooltipy project.

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

from collections import namedtuple

MooltipassParam = namedtuple("MooltipassParam",
                             "param, formatter, allowed_range")

# Uncomment for lots of debugging
#logging.basicConfig(level=logging.DEBUG)

class _Mooltipass(object):
    """Mooltipass -- Outlines access to Mooltipass's USB commands.

    This class is designed to be inherited (particularly by
    MooltipassClient()) and represents the server half of of the Client-
    Server / App-Mooltiplass relationship.
    """

    """valid_params contains a dictionary of all valid mooltipass
    configuration parameters and their internal mapping"""
    valid_params = {
            'keyboard_layout'    : MooltipassParam(KEYBOARD_LAYOUT_PARAM, hex, range(128+18, 128+39)),
            'user_intr_timer'    : MooltipassParam(USER_INTER_TIMEOUT_PARAM, int, range(0, 0xFF)),
            'lock_timeout_enable': MooltipassParam(LOCK_TIMEOUT_ENABLE_PARAM, bool, [0, 1]),
            'lock_timeout'       : MooltipassParam(LOCK_TIMEOUT_PARAM, int, range(0, 0xFF)),
            'touch_di'           : MooltipassParam(TOUCH_DI_PARAM, int, range(0, 0xFF)),
            # TOUCH_WHEEL_OS_PARAM_OLD - Not used anymore
            'touch_prox_os'      : MooltipassParam(TOUCH_PROX_OS_PARAM, hex, range(0, 0xFF)),
            'offline_mode'       : MooltipassParam(OFFLINE_MODE_PARAM, bool, [0, 1]),
            'screensaver'        : MooltipassParam(SCREENSAVER_PARAM, bool, [0, 1]),
            'touch_charge_time'  : MooltipassParam(TOUCH_CHARGE_TIME_PARAM, int, range(0, 0xFF)),
            'touch_wheel os_0'   : MooltipassParam(TOUCH_WHEEL_OS_PARAM0, hex, range(0, 0xFF)),
            'touch_wheel os_1'   : MooltipassParam(TOUCH_WHEEL_OS_PARAM1, hex, range(0, 0xFF)),
            'touch_wheel os_2'   : MooltipassParam(TOUCH_WHEEL_OS_PARAM2, hex, range(0, 0xFF)),
            'flash_screen'       : MooltipassParam(FLASH_SCREEN_PARAM, bool, [0, 1]),
            'user_req_cancel'    : MooltipassParam(USER_REQ_CANCEL_PARAM, bool, [0, 1]),
            'tutorial'           : MooltipassParam(TUTORIAL_BOOL_PARAM, bool, [0, 1]),
            'screen_saver_speed' : MooltipassParam(SCREEN_SAVER_SPEED_PARAM, int, range(0, 0xFF))
            }

    _PKT_LEN_INDEX = 0x00
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
        # Mostly ripped out of mooltipas_coms.py from the mooltipass
        # project originally written by Mathieu Stephan
        # https://github.com/limpkin/mooltipass/tools/python_comms/mooltipass_coms.py


        USB_VID = 0x16D0
        USB_PID = 0x09A0

        # Find the device
        self._hid_device = usb.core.find(idVendor=USB_VID, idProduct=USB_PID)

        if self._hid_device is None:
            raise RuntimeError('Mooltipass not found. Is it plugged in?')

        # Different init codes depending on the platform
        if platform.system() == "Linux":
            try:
                self._hid_device.detach_kernel_driver(0)
                self._hid_device.reset()
            except Exception as e:
                pass # Probably already detached
        else:
            # Set the active configuration. With no arguments, the first configuration will be the active one
            try:
                self._hid_device.set_configuration()
            except Exception as e:
                raise RuntimeError('Cannot set device configuration: ' + str(e))

        # Get an endpoint instance
        try:
            cfg = self._hid_device.get_active_configuration()
            self._intf = cfg[(0,0)]
        except Exception as e:
            raise RuntimeError('Could not get device config: ' + str(e))

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

        logging.debug('TX Packet: \n{}'.format(arraytosend))

        self._epout.write(arraytosend)

    def recv_packet(self, timeout=17500):
        """Receives a packet from the mooltipass.

        Keyword arguments:
            timeout -- how long to wait for user to complete entering pin
                    (default 17500 coincides with Mootipass GUI timeout)
        """
        recv = None
        while True:
            recv = self._epin.read(self._epin.wMaxPacketSize, timeout=timeout)
            #logging.debug('\n\t' + str(recv))
            if recv is not None:
                if recv[self._CMD_INDEX] == 0xB9:
                    # Unit sends 0xB9 when user is entering their PIN.
                    break
                elif recv[self._CMD_INDEX] == CMD_DEBUG:
                    debug_msg = struct.unpack('{}s'.format(recv[self._PKT_LEN_INDEX]-1), recv[self._DATA_INDEX:recv[self._PKT_LEN_INDEX]+1])[0]
                    if debug_msg == "#MBE":
                        print("Received Memory Boundary Error Callback!")
                    elif debug_msg == "#NM":
                        print("Received Node Mgmt Critical Error Callback!")
                    elif debug_msg == "#NMP":
                        print("Received Node Mgmt Permission Validity Error Callback!")
                    else:
                        print("Received unknown debug message {}".format(debug_msg))
                    print('Exiting...')
                    sys.exit(1)
                elif recv[self._CMD_INDEX] == 0xC4:
                    # The mooltipass may request the client resend its
                    # previous packet. I have not yet encountered this, but
                    # I guess it should be passed back to the calling
                    # function... alternatively we should mingle the send
                    # and receive methods or maybe create a FIFO pipe and
                    # "peek" at the contents in send before moving back to
                    # the calling function which would then recv_packet.
                    # One more thought, maybe just find out under what
                    # circumstances a 0xC4 may be received (e.g. data xfer
                    # only). Just leaving some thoughts.
                    print('HEY I GOT A 0xC4!')
                else:
                    break
            time.sleep(.5)
        logging.debug('RX Packet - CMD:0x{:x} Length:{}'.format(recv[self._CMD_INDEX], recv[self._PKT_LEN_INDEX]))
        logging.debug('{}'.format(recv[self._DATA_INDEX:]))
        # Data sent out of the generic HID is in the form of a 64 byte packet.
        # In most cases information is returned in the data portion of a packet
        # (the trailing 62 bytes). However, the first byte (byte 0) may contain
        # control information -- this could be a length indicator or boolean 
        # value.

        # Packet len includes the cmd byte, so subtract 1 to match the data len
        return recv[self._DATA_INDEX:], recv[self._PKT_LEN_INDEX]-1

    def ping(self, data):
        """Ping the mooltipass. (0xA1)

        Send up to 4 bytes of data to the mooltipass. The mooltipass
        replies by sending back the same values passed to it by the
        app (up to 4 bytes). If less than 4 bytes are sent to the
        mooltipass, the mooltipass replies with as many bytes as were
        provided, but the remaining of the 4 bytes will contain
        garbage.

        Arguments:
            data -- byte array to pass with ping command

        Returns None. It is client's responsibility to listen for
        responses matching the data sent with their ping request.

        IMPORTANT NOTE:
            Ping is not just a mechanism for testing connectivity to
            the mooltipass, it is a crucial element in initializing
            communication with. Failure to ping after connecting to
            the mooltipass can result in unpredictable responses.
        """
        self.send_packet(CMD_PING, data)
        return None

    def get_version(self):
        """Get mooltipass firmware version. (0xA2)

        Returns response from mooltipass:
            recv[0]  -- Size of response
            recv[1]  -- Response Command ID
            recv[2]  -- Byte contains the FLASH_CHIP define
                        specifying how much memory the unit has.
                        Eg. 4 == 4Mb
            recv[3:] -- String identifying the version.
                        Eg. "v1"
        """
        self.send_packet(CMD_VERSION, None)
        recv, data_len = self.recv_packet()
        # TODO: TEST THIS
        return struct.unpack('<b{}s'.format(data_len-1), recv[0:data_len])

    def set_context(self, context):
        """Set mooltipass context. (0xA3)

        Arguments:
            context -- string value containing context

        Returns response from mooltipass, a single byte:
            0 -- Mooltipass does not know context
            1 -- Context successfully set
            3 -- No card inserted into mooltipass
        """

        self.send_packet(CMD_CONTEXT, array('B', context + b'\x00'))
        recv, _ = self.recv_packet(10000)
        return recv[0]

    def get_login(self):
        """Get the login for current context. (0xA4)

        Returns the login as a string or 0 on failure.
        """
        self.send_packet(CMD_GET_LOGIN, None)
        recv, data_len = self.recv_packet()
        if recv[0] == 0:
            return 0
        else:
            return struct.unpack('<{}s'.format(data_len), recv[:data_len])[0]

    def get_password(self):
        """Get the password for current context. (0xA5)

        Returns the password as a string or 0 on failure.
        """
        self.send_packet(CMD_GET_PASSWORD, None)
        recv, data_len = self.recv_packet()
        if recv[0] == 0:
            return 0
        else:
            return struct.unpack('<{}s'.format(data_len), recv[:data_len])[0]

    def set_login(self, login):
        """Set a login. (0xA6)

        Return 1 or 0 indicating success or failure.
        """
        self.send_packet(CMD_SET_LOGIN, array('B', login + b'\x00'))
        recv, _ = self.recv_packet()
        return recv[0]

    def set_password(self, password):
        """Set a password for current context. (0xA7)

        Return 1 or 0 indicating success or failure.
        """
        self.send_packet(CMD_SET_PASSWORD, array('B', password + b'\x00'))
        recv, _ = self.recv_packet()
        return recv[0]

    def check_password(self, password):
        """Compare given password to set password for context. (0xA8)

        Call check_password() to avoid calling set_password() and
        prompting the user to overwrite a value that already exists.

        Returns 1 or 0 indicating success or failure.
        """
        recv = None
        # A timer blocks repeated checking of passwords.
        # A return of 0x02 means the timer is still counting down.
        while recv is None or recv == 0x02:
            self.send_packet(CMD_CHECK_PASSWORD, array('B', password + b'\x00'))
            recv, _ = self.recv_packet()
            recv = recv[0]
            time.sleep(.2)

        return recv

    def add_context(self, context):
        """Add a context. (0xA9)

        Return 1 or 0 indicating success or failure.
        """
        self.send_packet(CMD_ADD_CONTEXT, array('B', context + b'\x00'))
        recv, _ = self.recv_packet()
        return recv[0]
        # TODO: Is there any way to delete contexts?

    def _set_bootloader_password(self, password):
        """??? (0xAA)"""
        logging.info('Not yet implemented')
        pass

    def _jump_to_bootloader(self):
        """??? (0xAB)"""
        logging.info('Not yet implemented')
        pass

    def get_random_number(self):
        """Get 32 random bytes. (0xAC)"""
        # TODO: Is this intended to be directly used in generation of
        #   a random password, or as seed in external PRNG?
        self.send_packet(CMD_GET_RANDOM_NUMBER, None)
        recv, _ = self.recv_packet()
        return recv[0]

    def start_memory_management(self, timeout=20000):
        """Enter memory management mode. (0xAD)

        Keyword argument:
            timeout -- how long to wait for user to complete entering pin
                    (default 20000).

            Note: Mooltipass times out after ~17.5 seconds of inaction.
        """
        print('Accept memory management mode to continue...')
        self.send_packet(CMD_START_MEMORYMGMT, None)
        recv, _ = self.recv_packet(timeout)
        return recv[0]

    def _start_media_import(self):
        """Request send media to Mooltipass. (0xAE)

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def _media_import(self, data):
        """Send data to mooltipass. (0xAF)

        Send specially formatted data to the mooltipass as part of a
        media import. <DOCUMENT FORMAT HERE IF POSSIBLE>

        Return 1 or 0 indicating success or failure.
        """
        #TODO: Ask for pointer to source containing formatting!
        logging.info('Not yet implemented')
        pass

    def _end_media_import(self):
        """Request end media to Mooltipass. (0xB0)

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def _set_mooltipass_parameter(self, param_id, value):
        """Set a mooltipass parameter. (0xB1)

        Arguments:
            param_id - Parameter ID to set
            value - Value to set

        Return 1 or 0 indicating success or failure.
        """
        # TODO: Where are paremeters documented?
        logging.info('Not yet implemented')
        pass

    def _get_mooltipass_parameter(self, param_id):
        """Retrieve a mooltipass parameter (0xB2).

        Arguments:
            param_id -- Parameter ID to get

        Returns the parameter value.
        """
        logging.info('Not yet implemented')
        pass

    def _reset_card(self):
        """Reset inserted card. (0xB3)

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def _read_card_login(self):
        """Read login stored inside smartcard. (0xB4)

        Returns login or None.
        """
        logging.info('Not yet implemented')
        pass

    def _read_card_password(self):
        """Read password stored inside the smartcard. (0xB5)

        Mooltipass asks for confirmation.

        Returns password or None.
        """
        logging.info('Not yet implemented')
        pass

    def _set_card_login(self, login):
        """Set card login stored inside smartcard. (0xB6)

        Mooltipass asks for confirmation.

        Arguments:
            login -- Login value up to 62 bytes

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def _set_card_password(self, password):
        """Set password stored inside the smartcard. (0xB7)

        Mooltipass asks for confirmation.

        Arguments:
            password -- Password value up to 30 bytes.

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def _add_unknown_smartcard(self, cpz, ctr):
        """Instruct mooltipass to store an unknown smartcard. (0xB8)

        Arguments:
            ??? Not sure, experiment and review python_comms

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def get_status(self):
        """Return raw mooltipass status as int. (0xB9)

        The mooltipass returns a 1 byte bit field:
            Bit 0 -- Card presence
            Bit 1 -- Pin unlocking
            Bit 2 -- Card present and unlocked
            Bit 3 -- Unknown smart card inserted
        """
        # TODO: Interpret all bits; see /source_code/src/USB
        # Make constants, create list of invalid combinations and raise
        # error if encountered.
        self.send_packet(CMD_MOOLTIPASS_STATUS, None)
        recv, _ = self.recv_packet()
        return recv[0]

    # Where is 0xBA?

    def _set_date(self):
        """Set current date. (0xBB)"""
        loggin.info('Not yet implemented')
        pass

    def _set_mooltipass_uid(self):
        """Set the mooltipass UID. (0xBC)"""
        loggin.info('Not yet implemented')
        pass

    def _get_mooltipass_uid(self):
        """Get the mooltipass UID. (0xBD)"""
        loggin.info('Not yet implemented')
        pass

    def set_data_context(self, context):
        """Set the data context. (0xBE)

        Return 1 or 0 indicating success or failure.
        """
        self.send_packet(CMD_SET_DATA_SERVICE, array('B', context + b'\x00'))
        recv, _ = self.recv_packet()
        return recv[0]

    def add_data_context(self, context):
        """Add a data context. (0xBF)

        Arguments:
            context -- Name of context to add.

        Return 1 or 0 indicating success or failure.
        """
        print('sending ' + context)
        self.send_packet(CMD_ADD_DATA_SERVICE, array('B', context + b'\x00'))
        recv, _ = self.recv_packet()
        return recv[0]

    def write_data_context(self, data, callback=None):
        """Write to data context in blocks of 32 bytes. (0xC0)

        Data is sent to the mooltipass in 32 byte blocks. The the first
        byte of data sent with this command is an End of Data (EOD)
        marker. A non-zero value marks the data as the last block in
        sequence.

        After this EOD marker is 32 bytes of data making the total
        length of our transmission 33 bytes in size.

        Arguments:
            data -- iterable data to save in context
            callback -- function to receive tuple containing progress
                    in tuple form (x, y) where x is bytes sent and y
                    is size of transmission.

        Return true on success or raises RuntimeError if an unexpected
        response is received from the mooltipass.
        """

        BLOCK_SIZE = 32

        try:
            for i in range(0,len(data),BLOCK_SIZE):
                eod = (lambda byte: 0 if (len(data) - byte > BLOCK_SIZE) else 1)(i)
                packet = array('B')
                packet.append(eod)
                packet.extend(data[i:i+BLOCK_SIZE])
                self.send_packet(CMD_WRITE_32B_IN_DN, packet)
                if eod == 0 and not self.recv_packet()[0][0]:
                    raise RuntimeError('Unexpected return')
                if callback:
                    callback((i+32, len(data)))

            return True

        except (KeyboardInterrupt, SystemExit):
            self.send_packet(CMD_WRITE_32B_IN_DN, array('B').append(0))
            print('SENT TERMINATE')
            raise

    def read_data_context(self, callback=None):
        """Read data from context in blocks of 32 bytes. (0xC1)

        Get successive 32 byte blocks of data until EOD.

        Return data or None on error.
        """
        data = array('B')

        while True:
            self.send_packet(CMD_READ_32B_IN_DN, None)
            recv, data_len = self.recv_packet(5000)
            if data_len == 0x00:
                break
            data.extend(recv[:32])
            if callback:
                if len(data) == 32:
                    full_size = struct.unpack('>L', data[:4])[0]
                callback((len(data), full_size))

        return data

    def _get_current_card_cpz(self):
        """Return CPZ of currently inserted card.

        Card Protected Zone (CPZ)??? Returns None or data.
        """
        logging.info('Not yet implemented')
        # CPZ should be returned... presumably in 32 byte chunks in a
        # fashion simliar to reading data until 0x00 is encountered.
        # Mooltipass returns just 0x00 on error.
        pass

    def cancel_user_request(self):
        """Cancel user input request. (0xC3)

        The app can send a command to cancel any current user request.
        There's no receiving involved in this command, so None is
        always returned.
        """
        self.send_packet(CMD_CANCEL_USER_REQUEST, None)
        return None

    # 0xC4 is reserved for response from Mooltipass.

    def read_node(self, node_number):
        """Read a node in flash. (0xC5)

        Arguments:
            node_number - two bytes indicating node number

        Return the node or 0x00 on error.
        """
        node_addr = struct.pack('<H', node_number)
        data = array('B', node_addr)
        self.send_packet(CMD_READ_FLASH_NODE, data)

        recv, data_len = self.recv_packet()
        try:
            while data_len == 61:
                recv_extra, data_len = self.recv_packet()
                recv.extend(recv_extra)
        except usb.core.USBError:
            # Skip timeout once all packets are recieved
            pass

        return recv

    def _write_node(self, node_number, packet_number):
        """Write a node in flash. (0xC6)

        Arguments:
            node_number -- two bytes indicating the node number
            pckt_number -- ??? byte(s) indicating the node number

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def get_favorite(self, slot_id):
        """Get favorite for current user by slot ID. (0xC7)

        Arguments:
            slot_id -- Slot ID of favorite to retieve.

        Return None on error or parent_addr, child_addr tuple (each
        address is 2 bytes).
        """
        self.send_packet(CMD_GET_FAVORITE, array('B', [slot_id]))
        recv, _ = self.recv_packet()
        return struct.unpack('<HH', recv[0:4])

    def set_favorite(self, slot_id, addr_tuple):
        """Set a favorite. (0xC8)

        Arguments:
            slot_id - Slot ID of favorite to save / overwrite
            addr_tuple - parent_addr, child_addr tuple (each 2 bytes)

        Return 1 or 0 indicating success or failure.
        """
        logging.debug('Slot:{} Parent:0x{:x}{:x} Child:0x{:x}{:x}'.format(
                      slot_id,
                      addr_tuple[0]&0xFF, (addr_tuple[0]&0xFF00)>>8,
                      addr_tuple[1]&0xFF, (addr_tuple[1]&0xFF00)>>8))
        self.send_packet(CMD_SET_FAVORITE,
                         array('B', [slot_id, addr_tuple[0]&0xFF, (addr_tuple[0]&0xFF00)>>8, addr_tuple[1]&0xFF, (addr_tuple[1]&0xFF00)>>8]))
        recv, _ = self.recv_packet()
        return recv

    def get_starting_parent_address(self):
        """Get the address of starting parent? (0xC9)

        Return slot address or None on failure.
        """
        self.send_packet(CMD_GET_STARTING_PARENT, None)
        recv, _ = self.recv_packet()
        parent_addr = \
            struct.unpack('h', recv[:2])[0]
        return (lambda ret: None if 0 else ret)(parent_addr)

    def _set_starting_parent(self, parent_addr):
        """Set starting parent address. (0xCA)

        Arguments:
            parent_addr - 2 bytes starting parent address (LSB)

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass


    def _get_ctr_value(self):
        """Get the current user CTR value. (0xCB)

        Returns CTR value or None on error.
        """
        logging.info('Not yet implemented')
        pass

    def _set_ctr_value(self, ctr_value):
        """Set new CTR value. (0xCC)

        Arguments:
            ctr_value -- 3 byte CTR value

        Return 1 or 0 indicating success or failure.
        """
        logging.info('Not yet implemented')
        pass

    def add_cpz_ctr_value(self, cpz, ctr):
        pass
    def get_cpz_ctr_value(self):
        pass
    def cpz_ctr_packet_export(self):
        pass

    def get_free_slot_addresses(self, start_addr):
        """Scan for free slot addresses. (0xD0)

        Arguments:
            start_address - Address to start scanning from (if in doubt
                            0x00, 0x00).

        Return 31 slot addresses max otherwise (see payload length
        field)??? or None on error.
        """
        logging.info('Not yet implemented')
        pass

    def get_starting_data_parent_address(self):
        """Get the address of the data starting parent.

        Return slot address or None on failure.
        """
        self.send_packet(CMD_GET_DN_START_PARENT, None)
        recv, _ = self.recv_packet()
        parent_addr = \
            struct.unpack('h', recv[:2])[0]
        return (lambda ret: None if 0 else ret)(parent_addr)
        logging.info('Not yet implemented')
        pass

    def end_memory_management(self):
        """End memory management mode. (0xD3)

        Return 1 or 0 indicating success or failure."""
        print('Exiting memory management mode.')
        self.send_packet(CMD_END_MEMORYMGMT, None)
        recv, _ = self.recv_packet()
        return recv[0]

    def set_param(self, param, value):
        """Sets a setting on the mooltipass

        Returns 1 or 0 indicating success or failure."""
        self.send_packet(CMD_SET_MOOLTIPASS_PARM, array("B", [param, value]))
        recv, _ = self.recv_packet()
        return recv[0]

    def get_param(self, param):
        """Gets the value of a setting on the mooltipass

        Returns the setting value."""
        self.send_packet(CMD_GET_MOOLTIPASS_PARM, array("B", [param]))
        recv, _ = self.recv_packet()
        return recv[0]
