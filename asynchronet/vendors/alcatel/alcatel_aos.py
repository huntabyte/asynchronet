from typing import Any
from asynchronet.vendors.base import BaseDevice
from asynchronet.logger import logger
import asyncio
import re


class AlcatelAOS(BaseDevice):
    """Class for interacting with Alcatel AOS devices."""

    async def _read_until_prompt_or_pattern(self, pattern="", re_flags=0) -> Any:
        """
        Read until either self.base_pattern or pattern is detected.
        Return all data available
        """
        output = ""
        logger.info(f"Host {self._host}: Reading until prompt or pattern")
        if not pattern:
            pattern = self._base_pattern
        base_prompt_pattern = self._base_pattern
        while True:
            fut = self._stdout.read(self._MAX_BUFFER)
            try:
                output += await asyncio.wait_for(fut, self._timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(self._host)
            if re.search("\n" + pattern, output, flags=re_flags) or re.search(
                "\n" + base_prompt_pattern, output, flags=re_flags
            ):
                logger.debug(
                    f"Host {self._host}: Reading pattern '{pattern}'"
                    f"or '{base_prompt_pattern}' was found: {repr(output)}"
                )
                return output
