#!/usr/bin/env python
#
# Mooltipy development and example stub.

from mooltipy import MooltipassClient

import logging
import time
import sys


if __name__ == '__main__':

    logging.basicConfig(
            format='%(levelname)s\t %(funcName)s():\t %(message)s',
            level=logging.DEBUG)
            #level=logging.INFO)


    #hid_device, intf, epin, epout = findHIDDevice(USB_VID, USB_PID, True)
    mooltipass = MooltipassClient()

    if mooltipass is None:
        sys.exit(0)

    if not mooltipass.ping():
        logging.error('Mooltipass did not reply to a ping request!')
        print('failure')
        sys.exit(0)


    recv = mooltipass.status
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


    test_context = False
    if test_context:
        while not mooltipass.set_context(b'another_site2'):
            print(mooltipass.add_context(b'another_site2'))

        print(mooltipass.set_login(b'bob'))
        print(mooltipass.set_password(b'f2jf88288flskjf\x0D'))

    test_data = True
    if test_data:
        context = b'xdat45'
        while True:
            if mooltipass.set_data_context(context):
                print('set context')
                break
            print(b'adding context: ' + context)
            if not mooltipass.add_data_context(context):
                print('user decliend to add context.')
                sys.exit(0)

        from array import array
        #x = array('B', x[::-1])
        x = array('B')
        for i in range(0,512):
            x.append((512-i)%255)
            #x.append(i)

        #print(x)
        print('sending data -- length is: ' + str(len(x)))
        #mooltipass.write_data_context(x)
        time.sleep(2)

        print('reading...')
        mooltipass.read_data_context()

    print('fin')














