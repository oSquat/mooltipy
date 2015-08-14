#!/usr/bin/env python
#
# Mooltipy development and example stub.

from mooltipy import Mooltipass

import logging
import time
import sys


if __name__ == '__main__':

    logging.basicConfig(
            format='%(levelname)s\t %(funcName)s():\t %(message)s',
            level=logging.DEBUG)
            #level=logging.INFO)


    #hid_device, intf, epin, epout = findHIDDevice(USB_VID, USB_PID, True)
    mooltipass = Mooltipass()

    if mooltipass is None:
        sys.exit(0)

    if not mooltipass.ping():
        logging.error('Mooltipass did not reply to a ping request!')
        print('failure')
        sys.exit(0)


    #while True:
    #    recv = mooltipass.get_status()
    #    if recv is None:
    #        print('error')
    #    else:
    #        if recv[DATA_INDEX] == 0:
    #            print('No card inserted')
    #        elif recv[DATA_INDEX] == 1:
    #            # Also displays when car is incorrectly inserted
    #            print('Mooltipass locked')
    #        elif recv[DATA_INDEX] == 3:
    #            print('Mooltipass locked, unlocking screen')
    #        elif recv[DATA_INDEX] == 5:
    #            print('Mooltipass unlocked')
    #        elif recv[DATA_INDEX] == 9:
    #            print('Unknown smart card')
    #        else:
    #            print('unknown resp: {0}'.format(str(recv[DATA_INDEX])))

    #    time.sleep(2)

    recv = mooltipass.get_status()
    if recv is None:
        print('error')
    else:
        if recv == 0:
            print('No card inserted')
        elif recv == 1:
            # Also displays when car is incorrectly inserted
            print('Mooltipass locked')
        elif recv == 3:
            print('Mooltipass locked, unlocking screen')
        elif recv == 5:
            print('Mooltipass unlocked')
        elif recv == 9:
            print('Unknown smart card')
        else:
            print('unknown resp: {0}'.format(str(recv[DATA_INDEX])))

    #print(mooltipass.start_memory_management())

    #print(mooltipass.end_memory_management())

    while not mooltipass.set_context('another_site2'):
        print(mooltipass.add_context('another_site2'))

    print(mooltipass.set_login('bob'))
    print(mooltipass.set_password('f2jf88288flskjf\x0D'))

    print('fin')














