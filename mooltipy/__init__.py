#!/usr/bin/env python
#
# Mooltipy - a python library for the Mooltipass
#
# Mostly ripped out of mooltipas_coms.py from the mooltipass project (relative
# path /tools/python_comms/mooltipass_coms.py). This is my learning guide with
# a goal of creating a non-browser mooltipas management utility.
#
# If you are having difficulty with core stuff (e.g. establishing a connection
# to the mooltipass) it may be wise to compare with that file as I have trimmed
# things down for simplicity.

from array import array

import logging
import platform
import usb.core
import random
import sys
import time

CMD_PING = 0xa1

CMD_MOOLTIPASS_STATUS   = 0xB9

CMD_INDEX = 0x01
DATA_INDEX = 0x02

class Mooltipass(object):

    _epin = None
    _epout = None
    _hid_device = None

    _intf = None

    def __init__(self):

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


    def send_packet(self, cmd, data):
        """Sends generic HID a packet.

        epout?
        cmd is command identifier
        data is array or struct
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
        arraytosend.append(data_len)
        arraytosend.append(cmd)

        ##### Original code only appended command if it wasn't 0???
        ##### What is CMD 0 used for then, straight data transfer?

        if data is not None:
            arraytosend.extend(data)

        self._epout.write(arraytosend)


    def ping(self):
        """Ping the mooltipass. Returns True / False on success / failure."""

        try:
            # TODO: What other method for obtaining bytes than random can I use?
            #   Try milliseconds time.time() since we already need time module
            #   ...or maybe we can eliminate time from use instead probably no need
            send_data = array('B')
            send_data.append(random.randint(0,255))
            send_data.append(random.randint(0,255))

            self.send_packet(CMD_PING, send_data)

            recv = None
            while recv is None or \
                    recv[DATA_INDEX] != send_data[0] or \
                    recv[DATA_INDEX+1] != send_data[1]:

                recv = self._epin.read(self._epin.wMaxPacketSize, timeout=1000)

            logging.info("Mooltipass replied to our ping message")
            return True

        except usb.core.USBError as e:
            logging.error(e)
            return False


    def get_status(self):
        """Returns raw mooltipass status."""

        self.send_packet(CMD_MOOLTIPASS_STATUS, None)
        return self._epin.read(self._epin.wMaxPacketSize, timeout=10000)
