"""Subclass specific to Ubiquity Edge Switch"""
import re

from asynchronet.logger import logger
from asynchronet.vendors.ios_like import IOSLikeDevice


class UbiquityEdgeSwitch(IOSLikeDevice):
    """Class for working with Ubiquity Edge Switches"""

    _pattern = r"\({prompt}.*?\) (\(.*?\))?[{delimiters}]"
    """Pattern for using in reading buffer. When it found processing ends"""

    _config_enter = "configure"
    """Command for entering to configuration mode"""

    async def _set_base_prompt(self):
        """
        Setting two important vars
            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. IT's platform specific parameter

        For Ubiquity devices base_pattern is "(prompt) (\(.*?\))?[>|#]"
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
