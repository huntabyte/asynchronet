"""
Cisco Nexus support

For use with Cisco Nexus/NX-OS Devices

"""

import re

from asynchronet.vendors.ios_like import IOSLikeDevice


class CiscoNXOS(IOSLikeDevice):
    """Class for interacting with Cisco Nexus/NX-OS devices"""

    @staticmethod
    def _normalize_linefeeds(a_string):
        """
        Convert '\r\n' or '\r\r\n' to '\n, and remove extra '\r's in the text
        """
        newline = re.compile(r"(\r\r\n|\r\n)")

        return newline.sub("\n", a_string).replace("\r", "")
