"""Mooltipy - a python library for the Mooltipass.

Classes:
    Mooltipass -- Outlines access to Mooltipass's USB commands. This
                class is designed to be inherited (particularly by
                MooltipassClient()) and represents the server half of
                of the Client-Server / App-Mooltiplass relationship.
    MooltipassClient -- Certain USB commands the mooltipass makes
                available are not of use with out client-side logic.
                Some client-side code should be universal amongst apps
                and MooltipassClient() should be a layer fulfilling
                this need.

"""

from .mooltipass_client import MooltipassClient
