"""
Huawei Support

For use with Huawei Devices

"""

from asynchronet.vendors.comware_like import ComwareLikeDevice
import re
from asynchronet.logger import logger


class Huawei(ComwareLikeDevice):
    """Class for interacting with Huawei devices."""

    # Command to disable paging
    _disable_paging_command = "screen-length 0 temporary"

    async def _set_base_prompt(self):
        """
        Setting two important vars
            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For Comware devices base_pattern is "[\]|>]prompt(\-\w+)?[\]|>]
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        prompt = await self._find_prompt()
        # Strip off any leading HRP_. characters for USGv5 HA
        prompt = re.sub(r"^HRP_.", "", prompt, flags=re.M)
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
