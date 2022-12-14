"""
Cisco SG3XX support

For use with Cisco SG3XX Devices

"""
from asynchronet.vendors.ios_like import IOSLikeDevice


class CiscoSG3XX(IOSLikeDevice):
    """Class for interacting with Cisco SG3XX devices."""

    def __init__(self, *args, **kwargs):
        """
        Initialize class for asynchronous working with network devices

        :param str host: device hostname or ip address for connection
        :param str username: username for logging to device
        :param str password: user password for logging to device
        :param str secret: secret password for privilege mode
        :param int port: ssh port for connection.
            (default=22)
        :param str device_type: network device type
        :param known_hosts: file with known hosts.
            (default=None) With () it will use default file
        :param str local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys.
            (default=None) With () it will use default file in OS
        :param str passphrase: password for encrypted client keys
        :param float timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object
        """
        super().__init__(*args, **kwargs)
        self._ansi_escape_codes = True

    # Command to disable paging
    _disable_paging_command = "terminal datadump"
