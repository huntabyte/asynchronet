"""
HP Compare Limited support

For use with HP Compare Limited-like 1920 & 1920 devices

"""

from asynchronet.logger import logger
from asynchronet.vendors.comware_like import ComwareLikeDevice


class HPComwareLimited(ComwareLikeDevice):
    """Class for interacting with HP Comware Limited-like devices"""

    def __init__(self, cmdline_password="", *args, **kwargs):
        """
        Initialize  class for asynchronous working with network devices

        :param str host: device hostname or ip address for connection
        :param str username: username for logging to device
        :param str password: user password for logging to device
        :param str cmdline_password: password for entering to _cmd_line
        :param int port: ssh port for connection.
            (default=22)
        :param str device_type: network device type
        :param known_hosts: file with known hosts.
            (default=None) With () it will use the default file
        :param str local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys.
            (default=None) With () it will use the default file in OS
        :param str passphrase: password for encrypted client keys
        :param float timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object
        """
        super().__init__(*args, **kwargs)
        self._cmdline_password = cmdline_password

    # Command to enter cmdline mode
    _cmdline_mode_enter_command = "_cmdline-mode on"

    # String to check from wrong password when entering cmdline mode
    _cmdline_mode_check = "Invalid password"

    async def connect(self):
        """
        Basic asynchronous connection method

        It connects to device and makes some preparation steps for working.
        Usual using 4 functions:

        * _establish_connection() for connecting to device
        * _set_base_prompt() for finding and setting device prompt
        * _cmdline_mode_enter() for entering hidden full functional mode
        * _disable_paging() for non interact output in commands
        """
        logger.info(f"Host {self._host}: Trying to connect to the device")
        await self._establish_connection()
        await self._set_base_prompt()
        await self._cmdline_mode_enter()
        await self._disable_paging()
        logger.info(f"Host {self._host}: Has connected to the device")

    async def _cmdline_mode_enter(self):
        """Entering to cmdline-mode"""
        logger.info(f"Host {self._host}: Entering to cmdline mode")
        output = ""
        cmdline_mode_enter = type(self)._cmdline_mode_enter_command
        check_error_string = type(self)._cmdline_mode_check

        output = await self.send_command(cmdline_mode_enter, pattern="\[Y\/N\]")
        output += await self.send_command("Y", pattern="password\:")
        output += await self.send_command(self._cmdline_password)

        logger.debug(f"Host {self._host}: cmdline mode output: {repr(output)}")
        logger.info(f"Host {self._host}: Checking cmdline mode")
        if check_error_string in output:
            raise ValueError("Failed to enter to cmdline mode")

        return output
