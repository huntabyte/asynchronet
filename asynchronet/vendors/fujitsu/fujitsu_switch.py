"""
Fujitsu Switch support

For use with Fujitsu Blade Switches

"""
import re

from asynchronet.logger import logger
from asynchronet.vendors.ios_like import IOSLikeDevice


class FujitsuSwitch(IOSLikeDevice):
    """Class for working with Fujitsu Blade switch"""

    # Pattern to use when reading buffer. When found, processing ends.
    _pattern = r"\({prompt}.*?\) (\(.*?\))?[{delimiters}]"

    # Command to disable paging
    _disable_paging_command = "no pager"

    # Command to enter configuration mode
    _config_enter = "conf"

    async def _set_base_prompt(self):
        """
        Setting two important vars
            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For Fujitsu devices base_pattern is "(prompt) (\(.*?\))?[>|#]"
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

    @staticmethod
    def _normalize_linefeeds(a_string):
        """
        Convert '\r\r\n','\r\n', '\n\r' to '\n and remove extra '\n\n' in the text
        """
        newline = re.compile(r"(\r\r\n|\r\n|\n\r)")
        return newline.sub("\n", a_string).replace("\n\n", "\n")
