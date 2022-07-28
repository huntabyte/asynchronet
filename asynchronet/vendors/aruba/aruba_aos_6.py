"""Subclass specific to Aruba AOS 6.x"""

import re

from asynchronet.logger import logger
from asynchronet.vendors.ios_like import IOSLikeDevice


class ArubaAOS6(IOSLikeDevice):
    """Class for working with Aruba OS 6.X"""

    # Command to disable paging
    _disable_paging_command = "no paging"

    # Command to exit from config mode to privilege exec mode
    _config_exit = "end"

    # String to check in prompt - if exists - we're in configuration mode
    _config_check = ") (config"

    # Pattern to use when reading buffer. When found, processing ends.
    _pattern = r"\({prompt}.*?\) (\(.*?\))?\s?[{delimiters}]"

    async def _set_base_prompt(self):
        """
        Setting two important vars:

            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For Aruba AOS 6 devices base_pattern is "(prompt) (\(.*?\))?\s?[#|>]
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        prompt = await self._find_prompt()

        # Strip off trailing terminator
        self._base_prompt = prompt[1:-3]
        delimiters = map(re.escape, type(self)._delimiter_list)
        delimiters = r"|".join(delimiters)
        base_prompt = re.escape(self._base_prompt[:12])
        pattern = type(self)._pattern
        self._base_pattern = pattern.format(prompt=base_prompt, delimiters=delimiters)
        logger.debug(f"Host {self._host}: Base Prompt: {self._base_prompt}")
        logger.debug(f"Host {self._host}: Base Pattern: {self._base_pattern}")
        return self._base_prompt
