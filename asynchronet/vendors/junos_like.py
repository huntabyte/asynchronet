"""
JunOSLikeDevice Class is abstract class for JunOS-like devices

Connection Methods are based on AsyncSSH and should be run in an asyncio loop
"""

import re

from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice


class JunOSLikeDevice(BaseDevice):
    """
    JunOSLikeDevice Class for working with JunOS-like devices

    Juniper JunOS like devices typically have the following:

    * shell mode (csh).
        This is csh shell for FreeBSD. This mode is not covered by this Class.
    * cli mode (specific shell).
        The entire configuration is usual configured in this shell

    * operation mode.
        This mode is using for getting information from device
    * configuration mode.
        This mode is using for configuration system
    """

    # These characters will stop reading from buffer.(the end of the device prompt)
    _delimiter_list = ["%", ">", "#"]

    # Pattern to use when reading buffer. When found, processing ends.
    _pattern = r"\w+(\@[\-\w]*)?[{delimiters}]"

    # Command to disable paging
    _disable_paging_command = "set cli screen-length 0"

    # Command to enter configuration mode
    _config_enter = "configure"

    # Command to exit configuration mode & enter privilege exec mode
    _config_exit = "exit configuration-mode"

    # String to check in prompt = If exists - we're in configuration mode
    _config_check = "#"

    # Command to commit changes
    _commit_command = "commit"

    # Command to commit changes with a comment
    _commit_comment_command = "commit comment {}"

    async def _set_base_prompt(self):
        """
        Setting two important vars
            base_prompt - textual prompt in CLI (usually username or hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For JunOS devices base_pattern is "user(@[hostname])?[>|#]
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        prompt = await self._find_prompt()
        prompt = prompt[:-1]
        # Strip off trailing terminator
        if "@" in prompt:
            prompt = prompt.split("@")[1]
        self._base_prompt = prompt
        delimiters = map(re.escape, type(self)._delimiter_list)
        delimiters = r"|".join(delimiters)
        pattern = type(self)._pattern
        self._base_pattern = pattern.format(delimiters=delimiters)
        logger.debug(f"Host {self._host}: Base Prompt: {self._base_prompt}")
        logger.debug(f"Host {self._host}: Base Pattern: {self._base_pattern}")
        return self._base_prompt

    async def check_config_mode(self):
        """Checks if in configuration mode.

        Returns boolean"""
        logger.info(f"Host {self._host}: Checking configuration mode")
        check_string = type(self)._config_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return check_string in output

    async def config_mode(self):
        """Enters configuration mode"""
        logger.info(f"Host {self._host}: Entering to configuration mode")
        output = ""
        config_enter = type(self)._config_enter
        if not await self.check_config_mode():
            self._stdin.write(self._normalize_cmd(config_enter))
            output += await self._read_until_prompt()
            if not await self.check_config_mode():
                raise ValueError("Failed to enter to configuration mode")
        return output

    async def exit_config_mode(self):
        """Exits from configuration mode"""
        logger.info(f"Host {self._host}: Exiting from configuration mode")
        output = ""
        config_exit = type(self)._config_exit
        if await self.check_config_mode():
            self._stdin.write(self._normalize_cmd(config_exit))
            output += await self._read_until_prompt()
            if await self.check_config_mode():
                raise ValueError("Failed to exit from configuration mode")
        return output

    async def send_config_set(
        self,
        config_commands=None,
        with_commit=True,
        commit_comment="",
        exit_config_mode=True,
    ):
        """
        Sending configuration commands to device
        By default automatically exits/enters configuration mode.

        :param list config_commands: iterable string list with commands to apply
        to network devices in system view
        :param bool with_commit: if true, commits all changes after applying
        all config_commands
        :param string commit_comment: message for configuration commit
        :param bool exit_config_mode: If true, automatically quick configuration mode
        :return: The output of these commands
        """

        if config_commands is None:
            return ""

        # Send config commands
        output = await self.config_mode()
        output += await super().send_config_set(config_commands=config_commands)
        if with_commit:
            commit = type(self)._commit_command
            if commit_comment:
                commit = type(self)._commit_comment_command.format(commit_comment)

            self._stdin.write(self._normalize_cmd(commit))
            output += await self._read_until_prompt()

        if exit_config_mode:
            output += await self.exit_config_mode()

        output = self._normalize_linefeeds(output)
        logger.debug(f"Host {self._host}: Config commands output: {repr(output)}")
        return output
