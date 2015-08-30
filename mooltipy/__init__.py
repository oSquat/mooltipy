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

"""
Mooltipy - a python library for the Mooltipass.

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
