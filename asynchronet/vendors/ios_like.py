"""
IOSLikeDevice Class is abstract class for using in Cisco IOS like devices

Connection Method are based upon AsyncSSH and should be running in asyncio loop
"""

import re

from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice


class IOSLikeDevice(BaseDevice):
    """
    This Class is abstract class for working with Cisco IOS like devices

    Cisco IOS like devices having several concepts:

    * user exec or unprivileged exec:
        This mode allows you perform basic tests and get system information.
    * privilege exec:
        This mode allows the use of all EXEC mode commands available on the system
    * configuration mode or config mode:
        This mode are used for configuration whole system.
    """

    def __init__(self, secret="", *args, **kwargs):
        """
        Initialize class for asynchronous working with network devices

        :param str host: device hostname or ip address for connection
        :param str username: username for logging to device
        :param str password: user password for logging to device
        :param str secret: secret password for privilege mode
        :param int port: ssh port for connection. Default is 22
        :param str device_type: network device type
        :param known_hosts: file with known hosts.
            Default is None (no policy). With () it will use default file
        :param str local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys.
            Default is None. With () it will use default file in OS
        :param str passphrase: password for encrypted client keys
        :param float timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object
        """
        super().__init__(*args, **kwargs)
        self._secret = secret

    # Command to enter privilege exec
    _priv_enter = "enable"

    # Command to exit privilege exec to user exec
    _priv_exit = "disable"

    # String to check in prompt - If exists - we're in privilege exec mode
    _priv_check = "#"

    # Command to enter configuration mode
    _config_enter = "conf t"

    # Command to exit configuration mode to privilege exec mode
    _config_exit = "end"

    # String to check in prompt - If exists - we're in configuration mode
    _config_check = ")#"

    async def connect(self):
        """
        Basic asynchronous connection method for Cisco IOS like devices

        It connects to device and makes some preparation steps for working.
        Usual using 4 functions:

        * _establish_connection() for connecting to device
        * _set_base_prompt() for finding and setting device prompt
        * _enable() for getting privilege exec mode
        * _disable_paging() for non interact output in commands
        """
        logger.info(f"Host {self._host}: Trying to connect to the device")
        await self._establish_connection()
        await self._set_base_prompt()
        await self.enable_mode()
        await self._disable_paging()
        logger.info(f"Host {self._host}: Has connected to the device")

    async def check_enable_mode(self):
        """Check if we are in privilege exec. Return boolean"""
        logger.info(f"Host {self._host}: Checking privilege exec")
        check_string = type(self)._priv_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return check_string in output

    async def enable_mode(self, pattern="password", re_flags=re.IGNORECASE):
        """Enter to privilege exec"""
        logger.info(f"Host {self._host}: Entering to privilege exec")
        output = ""
        enable_command = type(self)._priv_enter
        if not await self.check_enable_mode():
            self._stdin.write(self._normalize_cmd(enable_command))
            output += await self._read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )
            if re.search(pattern, output, re_flags):
                self._stdin.write(self._normalize_cmd(self._secret))
                output += await self._read_until_prompt()
            if not await self.check_enable_mode():
                raise ValueError("Failed to enter to privilege exec")
        return output

    async def exit_enable_mode(self):
        """Exit from privilege exec"""
        logger.info(f"Host {self._host}: Exiting from privilege exec")
        output = ""
        exit_enable = type(self)._priv_exit
        if await self.check_enable_mode():
            self._stdin.write(self._normalize_cmd(exit_enable))
            output += await self._read_until_prompt()
            if await self.check_enable_mode():
                raise ValueError("Failed to exit from privilege exec")
        return output

    async def check_config_mode(self):
        """Checks if the device is in configuration mode or not"""
        logger.info(f"Host {self._host}: Checking configuration mode")
        check_string = type(self)._config_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return check_string in output

    async def config_mode(self):
        """Enter into config_mode"""
        logger.info(f"Host {self._host}: Entering to configuration mode")
        output = ""
        config_command = type(self)._config_enter
        if not await self.check_config_mode():
            self._stdin.write(self._normalize_cmd(config_command))
            output = await self._read_until_prompt()
            if not await self.check_config_mode():
                raise ValueError("Failed to enter to configuration mode")
        return output

    async def exit_config_mode(self):
        """Exit from configuration mode"""
        logger.info(f"Host {self._host}: Exiting from configuration mode")
        output = ""
        exit_config = type(self)._config_exit
        if await self.check_config_mode():
            self._stdin.write(self._normalize_cmd(exit_config))
            output = await self._read_until_prompt()
            if await self.check_config_mode():
                raise ValueError("Failed to exit from configuration mode")
        return output

    async def send_config_set(self, config_commands=None, exit_config_mode=True):
        """
        Sending configuration commands to Cisco IOS like devices
        Automatically exits/enters configuration mode.

        :param list config_commands: iterable string list with commands
        to apply to network devices in conf mode
        :param bool exit_config_mode: If true, automatically quit configuration mode
        :return: The output of this commands
        """

        if config_commands is None:
            return ""

        # Send config commands
        output = await self.config_mode()
        output += await super().send_config_set(config_commands=config_commands)

        if exit_config_mode:
            output += await self.exit_config_mode()

        output = self._normalize_linefeeds(output)
        logger.debug(f"Host {self._host}: Config commands output: {repr(output)}")
        return output

    async def _cleanup(self):
        """Any needed cleanup before closing connection"""
        logger.info(f"Host {self._host}: Cleanup session")
        await self.exit_config_mode()
