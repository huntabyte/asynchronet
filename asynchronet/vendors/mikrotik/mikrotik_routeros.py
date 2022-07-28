import asyncssh
import asyncio

from asynchronet.exceptions import DisconnectError, TimeoutError
from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice


class MikrotikRouterOS(BaseDevice):
    """Class for working with Mikrotik RouterOS"""

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize class for asynchronous working with network devices
        Invoke init with some special params (base_pattern and username)

        :param str host: device hostname or ip address for connection
        :param str username: username for logging to device
        :param str password: user password for logging to device
        :param int port: ssh port for connection. Default is 22
        :param str device_type: network device type
        :param known_hosts: file with known hosts. Default is None (no policy).
            With () it will use default file
        :param str local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys. Default in None.
            With () it will use default file in OS
        :param str passphrase: password for encrypted client keys
        :param float timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object

        Mikrotik duplicate prompt in connection, so we should use pattern like
        prompt .* prompt.
        For disabling colors in CLI output we should user this username = username+c
        '+c' disables colors
        '+t' disable auto term capabilities detection
        '+200w' set terminal width to 200 rows
        """
        super().__init__(*args, **kwargs)
        self._base_pattern = r"\[.*?\] \>.*\[.*?\] \>"
        self._connect_params_dict["username"] += "+ct200w"
        self._ansi_escape_codes = True

    _pattern = r"\[.*?\] (\/.*?)?\>"

    async def connect(self) -> None:
        """
        Async Connection method

        RouterOS using 2 functions:

        * _establish_connection() for connecting to device
        * _set_base_prompt() for finding and setting device prompt
        """
        logger.info(f"Host {self._host}: Connecting to device")
        await self._establish_connection()
        await self._set_base_prompt()
        logger.info(f"Host {self._host}: Connected to device")

    async def _establish_connection(self):
        """Establish SSH connection to the network device"""
        logger.info(f"Host {self._host}: Establishing connection to port {self._port}")
        output = ""
        # initiate SSH connection
        fut = asyncssh.connect(**self._connect_params_dict)
        try:
            self._conn = await asyncio.wait_for(fut, self._timeout)
        except asyncssh.DisconnectError as e:
            raise DisconnectError(self._host, e.code, e.reason)
        except asyncio.TimeoutError:
            raise TimeoutError(self._host)
        self._stdin, self._stdout, self._stderr = await self._conn.open_session(
            term_type="Dumb"
        )
        logger.info(f"Host {self._host}: Connection is established")
        # Flush unnecessary data
        output = await self._read_until_prompt()
        logger.debug(f"Host {self._host}: Establish Connection Output: {repr(output)}")
        return output

    async def _set_base_prompt(self):
        """
        Setting two important vars
        * base_prompt - textual prompt in CLI (usually hostname)
        * base_pattern - regexp for finding the end of command. (platform-specific)

        For Mikrotik devices base_pattern is "r"\[.*?\] (\/.*?)?\>"
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        self._base_pattern = type(self)._pattern
        prompt = await self._find_prompt()
        # Strip off trailing terminator
        prompt = prompt[1:-3]
        if "@" in prompt:
            prompt = prompt.split("@")[1]
        self._base_prompt = prompt
        logger.debug(f"Host {self._host}: Base Prompt: {self._base_prompt}")
        logger.debug(f"Host {self._host}: Base Pattern: {self._base_pattern}")
        return self._base_prompt

    async def _find_prompt(self):
        """Finds the current network device prompt, last line only."""
        logger.info(f"Host {self._host}: Finding prompt")
        self._stdin.write("\r")
        prompt = ""
        prompt = await self._read_until_prompt()
        prompt = prompt.strip()
        if self._ansi_escape_codes:
            prompt = self._strip_ansi_escape_codes(prompt)
        if not prompt:
            raise ValueError(f"Unable to find prompt: {prompt}")
        logger.debug(f"Host {self._host}: Prompt: {prompt}")
        return prompt

    @staticmethod
    def _normalize_cmd(command):
        """Specific trailing newline for Mikrotik"""
        command = command.rstrip("\n")
        command += "\r"
        return command
