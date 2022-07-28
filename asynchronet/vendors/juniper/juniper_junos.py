from asynchronet.logger import logger
from asynchronet.vendors.junos_like import JunOSLikeDevice


class JuniperJunOS(JunOSLikeDevice):
    """Class for working with Juniper JunOS"""

    # String to check for shell mode
    _cli_check = ">"

    # Command to enter CLI mode
    _cli_command = "cli"

    async def connect(self):
        """
        Juniper JunOS asynchronous connection method

        It connects to device and makes some preparation steps for working:

        * _establish_connection() for connecting to device
        * cli_mode() for checking shell mode. If in shell - automatically enter CLI
        * _set_base_prompt() for finding and setting device prompt
        * _disable_paging() for non interact output in commands
        """
        logger.info(f"Host {self._host}: Trying to connect to the device")
        await self._establish_connection()
        await self._set_base_prompt()
        await self.cli_mode()
        await self._disable_paging()
        logger.info(f"Host {self._host}: Entering to cmdline mode")

    async def check_cli_mode(self):
        """Check if in CLI mode

        Return boolean"""
        logger.info(f"Host {self._host}: Checking shell mode")
        cli_check = type(self)._cli_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return cli_check in output

    async def cli_mode(self):
        """Enter CLI mode"""
        logger.info(f"Host {self._host}: Entering to cli mode")
        output = ""
        cli_command = type(self)._cli_command
        if not await self.check_cli_mode():
            self._stdin.write(self._normalize_cmd(cli_command))
            output += await self._read_until_prompt()
            if not await self.check_cli_mode():
                raise ValueError("Failed to enter to cli mode")
        return output
