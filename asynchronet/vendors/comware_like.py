"""
ComwareLikeDevice Class is abstract class for Comware-like devices

Connection Methods are based on AsyncSSH and should be run in an asyncio loop
"""

import re

from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice


class ComwareLikeDevice(BaseDevice):
    """
    This Class for working with hp comware like devices

    HP Comware like devices having several concepts:

    * user exec or user view. This mode is using for getting information from device
    * system view. This mode is using for configuration system
    """

    # These characters will stop reading from buffer.(the end of the device prompt)
    _delimiter_list = [">", "]"]

    # Beginning prompt characters. Prompt must contain these
    _delimiter_left_list = ["<", "["]

    # Pattern to use when reading buffer. When found, processing ends.
    _pattern = r"[{delimiter_left}]{prompt}[\-\w]*[{delimiter_right}]"

    # Command to disable paging
    _disable_paging_command = "screen-length disable"

    # Command to enter system view
    _system_view_enter = "system-view"

    # Command to return from system view to user view
    _system_view_exit = "return"

    # Check string in prompt. If it exists - we're in system view
    _system_view_check = "]"

    async def _set_base_prompt(self):
        """
        Setting two important vars
            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For Comware devices base_pattern is "[\]|>]prompt(\-\w+)?[\]|>]
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        prompt = await self._find_prompt()
        # Strip off trailing terminator
        self._base_prompt = prompt[1:-1]
        delimiter_right = map(re.escape, type(self)._delimiter_list)
        delimiter_right = r"|".join(delimiter_right)
        delimiter_left = map(re.escape, type(self)._delimiter_left_list)
        delimiter_left = r"|".join(delimiter_left)
        base_prompt = re.escape(self._base_prompt[:12])
        pattern = type(self)._pattern
        self._base_pattern = pattern.format(
            delimiter_left=delimiter_left,
            prompt=base_prompt,
            delimiter_right=delimiter_right,
        )
        logger.debug(f"Host {self._host}: Base Prompt: {self._base_prompt}")
        logger.debug(f"Host {self._host}: Base Pattern: {self._base_pattern}")
        return self._base_prompt

    async def _check_system_view(self):
        """Check if we are in system view. Return boolean"""
        logger.info(f"Host {self._host}: Checking system view")
        check_string = type(self)._system_view_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return check_string in output

    async def _system_view(self):
        """Enter to system view"""
        logger.info(f"Host {self._host}: Entering to system view")
        output = ""
        system_view_enter = type(self)._system_view_enter
        if not await self._check_system_view():
            self._stdin.write(self._normalize_cmd(system_view_enter))
            output += await self._read_until_prompt()
            if not await self._check_system_view():
                raise ValueError("Failed to enter to system view")
        return output

    async def _exit_system_view(self):
        """Exit from system view"""
        logger.info(f"Host {self._host}: Exiting from system view")
        output = ""
        system_view_exit = type(self)._system_view_exit
        if await self._check_system_view():
            self._stdin.write(self._normalize_cmd(system_view_exit))
            output += await self._read_until_prompt()
            if await self._check_system_view():
                raise ValueError("Failed to exit from system view")
        return output

    async def send_config_set(self, config_commands=None, exit_system_view=False):
        """
        Sending configuration commands to device
        Automatically exits/enters system-view.

        :param list config_commands: iterable string list with commands to apply
        to network devices in system view
        :param bool exit_system_view: If true, quit from system view automatically
        :return: The output of these commands
        """

        if config_commands is None:
            return ""

        # Send config commands
        output = await self._system_view()
        output += await super().send_config_set(config_commands=config_commands)

        if exit_system_view:
            output += await self._exit_system_view()

        output = self._normalize_linefeeds(output)
        logger.debug(f"Host {self._host,}: Config commands output: {repr(output)}")
        return output
