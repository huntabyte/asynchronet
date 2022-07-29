"""
The autodetect module is used to automatically detect the device_type required
to initiate a new SSH connection with the remote host.

The **SSHDetect** class is instantiated with the same parameters as a standard
asynchronet device. The only acceptable value for the `device_type` argument
is `autodetect`.

Incorporation of this capability was achieved by using existing the code from the
autodetect module within Netmiko (https://github.com/ktbyers/netmiko).
The code was slightly modified to support asynchronous operations.
"""

import asyncio
from asyncio import AbstractEventLoop
from socket import AF_UNSPEC, AF_INET, AF_INET6

from typing import Union
import re
from typing import Dict, List, Optional

import asyncssh
from asyncssh import SSHKnownHosts


from asynchronet.exceptions import TimeoutError, DisconnectError
from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice

SSH_MAPPER_DICT = {
    "alcatel_aos": {
        "cmd": "show system",
        "search_patterns": [r"Alcatel-Lucent"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "alcatel_sros": {
        "cmd": "show version",
        "search_patterns": ["Nokia", "Alcatel"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "apresia_aeos": {
        "cmd": "show system",
        "search_patterns": ["Apresia"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "arista_eos": {
        "cmd": "show version",
        "search_patterns": [r"Arista"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "ciena_saos": {
        "cmd": "software show",
        "search_patterns": [r"saos"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_asa": {
        "cmd": "show version",
        "search_patterns": [r"Cisco Adaptive Security Appliance", r"Cisco ASA"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_ios": {
        "cmd": "show version",
        "search_patterns": [
            "Cisco IOS Software",
            "Cisco Internetwork Operating System Software",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_ios_xe": {
        "cmd": "show version",
        "search_patterns": [
            "Cisco IOS XE Software",
            "Cisco IOS-XE software",
            "IOS-XE ROMMON",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_nxos": {
        "cmd": "show version",
        "search_patterns": [r"Cisco Nexus Operating System", r"NX-OS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_xr": {
        "cmd": "show version",
        "search_patterns": [r"Cisco IOS XR"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_force10": {
        "cmd": "show version",
        "search_patterns": [r"Real Time Operating System Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_os9": {
        "cmd": "show system",
        "search_patterns": [
            r"Dell Application Software Version:  9",
            r"Dell Networking OS Version : 9",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_os10": {
        "cmd": "show version",
        "search_patterns": [r"Dell EMC Networking OS10.Enterprise"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "dell_powerconnect": {
        "cmd": "show system",
        "search_patterns": [r"PowerConnect"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "f5_tmsh": {
        "cmd": "show sys version",
        "search_patterns": [r"BIG-IP"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "f5_linux": {
        "cmd": "cat /etc/issue",
        "search_patterns": [r"BIG-IP"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "hp_comware": {
        "cmd": "display version",
        "search_patterns": ["HPE Comware", "HP Comware"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "huawei": {
        "cmd": "display version",
        "search_patterns": [
            r"Huawei Technologies",
            r"Huawei Versatile Routing Platform Software",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "juniper_junos": {
        "cmd": "show version",
        "search_patterns": [
            r"JUNOS Software Release",
            r"JUNOS .+ Software",
            r"JUNOS OS Kernel",
            r"JUNOS Base Version",
        ],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "linux": {
        "cmd": "uname -a",
        "search_patterns": [r"Linux"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_exos": {
        "cmd": "show version",
        "search_patterns": [r"ExtremeXOS"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_netiron": {
        "cmd": "show version",
        "search_patterns": [r"(NetIron|MLX)"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_slx": {
        "cmd": "show version",
        "search_patterns": [r"SLX-OS Operating System Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "extreme_tierra": {
        "cmd": "show version",
        "search_patterns": [r"TierraOS Software"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "ubiquiti_edgeswitch": {
        "cmd": "show version",
        "search_patterns": [r"EdgeSwitch"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "cisco_wlc_85": {
        "cmd": "show inventory",
        "dispatch": "_autodetect_std",
        "search_patterns": [r"Cisco Wireless Controller"],
        "priority": 99,
    },
    "mellanox_mlnxos": {
        "cmd": "show version",
        "search_patterns": [r"Onyx", r"SX_PPC_M460EX"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "yamaha": {
        "cmd": "show copyright",
        "search_patterns": [r"Yamaha Corporation"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "fortinet": {
        "cmd": "get system status",
        "search_patterns": [r"FortiOS", r"FortiGate"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "paloalto_panos": {
        "cmd": "show system info",
        "search_patterns": [r"model:\s+PA"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "supermicro_smis": {
        "cmd": "show system info",
        "search_patterns": [r"Super Micro Computer"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
    "flexvnf": {
        "cmd": "show system package-info",
        "search_patterns": [r"Versa FlexVNF"],
        "priority": 99,
        "dispatch": "_autodetect_std",
    },
}

# Sort SSH_MAPPER_DICT such that the most common commands are first
cmd_count: Dict[str, int] = {}
for k, v in SSH_MAPPER_DICT.items():
    my_cmd = v["cmd"]
    assert isinstance(my_cmd, str)
    count = cmd_count.setdefault(my_cmd, 0)
    cmd_count[my_cmd] = count + 1
cmd_count = {k: v for k, v in sorted(cmd_count.items(), key=lambda item: item[1])}

# SSH_MAPPER_BASE is a list
SSH_MAPPER_BASE = sorted(
    SSH_MAPPER_DICT.items(), key=lambda item: int(cmd_count[str(item[1]["cmd"])])
)
SSH_MAPPER_BASE.reverse()


class SSHDetect(object):
    """
    Base Abstract Class for interacting with network devices
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str | None = None,
        port: int = 22,
        device_type: str = "",
        timeout: int = 15,
        loop: AbstractEventLoop | None = None,
        known_hosts: str | list[str] | bytes | SSHKnownHosts | None = None,
        local_addr: tuple[str, int] | None = None,
        client_keys: str | list[str] | list[tuple[str | bytes, str | bytes]] = None,
        passphrase: str | None = None,
        tunnel: BaseDevice | None = None,
        pattern: str | None = None,
        agent_forwarding: bool = False,
        agent_path: str | None = None,
        client_version: str = "asynchronet",
        family: AF_INET | AF_INET6 | AF_UNSPEC = 0,
        kex_algs: list[str] | None = None,
        encryption_algs: list[str] | None = None,
        mac_algs: list[str] | None = None,
        compression_algs: list[str] | None = None,
        signature_algs: list[str] | None = None,
        server_host_key_algs: list[str] | None = None,
    ):
        """
        Initialize base class for establishing asynchronous ssh connections to devices

        :param host: device hostname or ip address for connection
        :param username: username for logging to device
        :param password: user password for logging to device
        :param port: ssh port for connection. Default is 22
        :param device_type: network device type
        :param timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object
        :param known_hosts: file with known hosts. Default is None (no policy).
            With () it will use default file
        :param local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys. Default in None.
            With () it will use default file in OS
        :param passphrase: password for encrypted client keys
        :param tunnel: An existing SSH connection that this new connection
            should be tunneled over
        :param pattern: pattern for searching the end of device prompt.
                Example: r"{hostname}.*?(\(.*?\))?[{delimeters}]"
        :param agent_forwarding: Allow or not allow agent forward for server
        :param agent_path:
            The path of a UNIX domain socket to use to contact an ssh-agent
            process which will perform the operations needed for client
            public key authentication. If this is not specified and the environment
            variable `SSH_AUTH_SOCK` is set, its value will be used as the path.
            If `client_keys` is specified or this argument is explicitly set to `None`,
            an ssh-agent will not be used.
        :param client_version: version which advertised to ssh server
        :param family:
           The address family to use when creating the socket. By default,
           the address family is automatically selected based on the host.
        :param kex_algs:
            A list of allowed key exchange algorithms in the SSH handshake,
            taken from `key exchange algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#kexalgs>`_
        :param encryption_algs:
            A list of encryption algorithms to use during the SSH handshake,
            taken from `encryption algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#encryptionalgs>`_
        :param mac_algs:
            A list of MAC algorithms to use during the SSH handshake, taken
            from `MAC algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#macalgs>`_
        :param compression_algs:
            A list of compression algorithms to use during the SSH handshake,
            taken from `compression algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#compressionalgs>`_, or
            `None` to disable compression
        :param signature_algs:
            A list of public key signature algorithms to use during the SSH
            handshake, taken from `signature algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#signaturealgs>`_
        :param server_host_key_algs:
            A list of server host key algorithms to allow during the SSH handshake,
            taken from server host key algorithms.
            https://asyncssh.readthedocs.io/en/latest/api.html#publickeyalgs


        :type host: str
        :type username: str
        :type password: str
        :type port: int
        :type device_type: str
        :type timeout: int
        :type known_hosts:
            *see* `SpecifyingKnownHosts
            <https://asyncssh.readthedocs.io/en/latest/api.html#specifyingknownhosts>`_
        :type loop: :class:`AbstractEventLoop <asyncio.AbstractEventLoop>`
        :type pattern: str
        :type tunnel: :class:`BaseDevice <netdev.vendors.BaseDevice>`
        :type family:
            :class:`socket.AF_UNSPEC` or :class:`socket.AF_INET`
            or :class:`socket.AF_INET6`
        :type local_addr: tuple(str, int)
        :type client_keys:
            *see* `SpecifyingPrivateKeys
            <https://asyncssh.readthedocs.io/en/latest/api.html#specifyingprivatekeys>`_
        :type passphrase: str
        :type agent_path: str
        :type agent_forwarding: bool
        :type client_version: str
        :type kex_algs: list[str]
        :type encryption_algs: list[str]
        :type mac_algs: list[str]
        :type compression_algs: list[str]
        :type signature_algs: list[str]
        :type server_host_key_algs: list[str]
        """
        if device_type != "autodetect":
            raise ValueError("The connection device_type must be 'autodetect'")

        if host:
            self._host = host
        else:
            raise ValueError("Host must be set")
        self._port = int(port)
        self._device_type = device_type
        self._timeout = timeout
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop

        # Convert required connect params to a dict for simplicity
        self._connect_params_dict = {
            "host": self._host,
            "port": self._port,
            "username": username,
            "password": password,
            "known_hosts": known_hosts,
            "local_addr": local_addr,
            "client_keys": client_keys,
            "passphrase": passphrase,
            "tunnel": tunnel,
            "agent_forwarding": agent_forwarding,
            "family": family,
            "agent_path": agent_path,
            "client_version": client_version,
            "kex_algs": kex_algs,
            "encryption_algs": encryption_algs,
            "mac_algs": mac_algs,
            "compression_algs": compression_algs,
            "signature_algs": signature_algs,
        }

        if pattern is not None:
            self._pattern = pattern

        # A list of server host key algorithms to use instead of the default of
        # those present in known_hosts when performing the SSH handshake.
        # This should only be set, when the user sets it.
        if server_host_key_algs is not None:
            self._connect_params_dict["server_host_key_algs"] = server_host_key_algs

        self.potential_matches: Dict[str, int] = {}
        # Filling internal vars
        self._stdin = self._stdout = self._stderr = self._conn = None
        self._base_prompt = self._base_pattern = ""
        self._MAX_BUFFER = 65535
        self._ansi_escape_codes = False

    # These characters will stop reading from buffer.(the end of the device prompt)
    _delimiter_list = [">", "#"]

    # Pattern to use when reading buffer. When found, processing ends.
    _pattern = r"{prompt}.*?(\(.*?\))?[{delimiters}]"

    # Command to disable paging
    _disable_paging_command = "terminal length 0"

    @property
    def base_prompt(self):
        """Returns the base prompt for the network device"""
        return self._base_prompt

    async def __aenter__(self):
        """Async Context Manager Enter"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async Context Manager Exit"""
        await self.disconnect()

    async def connect(self):
        """
        Basic asynchronous connection method

        It connects to device and makes preparation steps for functionality.
        Typically using 3 functions:

        * _establish_connection() for connecting to device
        * _set_base_prompt() for finding and setting device prompt
        * _disable_paging() for non interactive output in commands
        """
        logger.info(f"Host {self._host}: Trying to connect to the device")
        await self._establish_connection()
        await self._set_base_prompt()
        await self._disable_paging()
        logger.info(f"Host {self._host}: Has connected to the device")

    async def autodetect(self) -> Union[str, None]:
        """
        Try to guess the best 'device_type' based on patterns defined in SSH_MAPPER_BASE

        Returns
        -------
        best_match : str or None
            The device type that is currently the best to use
            to interact with the device
        """
        await self.connect()
        for device_type, autodetect_dict in SSH_MAPPER_BASE:
            tmp_dict = autodetect_dict.copy()
            call_method = tmp_dict.pop("dispatch")
            assert isinstance(call_method, str)
            autodetect_method = getattr(self, call_method)
            accuracy = await autodetect_method(**tmp_dict)
            if accuracy:
                self.potential_matches[device_type] = accuracy
                # Stop the loop as we are sure of our match
                best_match = sorted(
                    self.potential_matches.items(), key=lambda t: t[1], reverse=True
                )
                # WLC needs two different auto-dectect solutions
                if "cisco_wlc_85" in best_match[0]:
                    best_match[0] = ("cisco_wlc", 99)

                await self.disconnect()
                return best_match[0][0]

    async def _establish_connection(self):
        """Establishes SSH connection to the network device"""
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
            term_type="Dumb", term_size=(200, 24)
        )
        logger.info(f"Host {self._host}: Connection is established")
        # Flush unnecessary data
        delimiters = map(re.escape, type(self)._delimiter_list)
        delimiters = r"|".join(delimiters)
        output = await self._read_until_pattern(delimiters)
        logger.debug(f"Host {self._host}: Establish Connection Output: {repr(output)}")
        return output

    async def _set_base_prompt(self):
        """
        Sets two important vars:

            base_prompt - textual prompt in CLI (usually hostname)
            base_pattern - regexp for finding the end of command. (platform-specific)

        For Cisco devices base_pattern is "prompt(\(.*?\))?[#|>]
        """
        logger.info(f"Host {self._host}: Setting base prompt")
        prompt = await self._find_prompt()

        # Strip off trailing terminator
        self._base_prompt = prompt[:-1]
        delimiters = map(re.escape, type(self)._delimiter_list)
        delimiters = r"|".join(delimiters)
        base_prompt = re.escape(self._base_prompt[:12])
        pattern = type(self)._pattern
        self._base_pattern = pattern.format(prompt=base_prompt, delimiters=delimiters)
        logger.debug(f"Host {self._host}: Base Prompt: {self._base_prompt}")
        logger.debug(f"Host {self._host}: Base Pattern: {self._base_pattern}")
        return self._base_prompt

    async def _disable_paging(self):
        """Disables paging method"""
        logger.info(f"Host {self._host}: Trying to disable paging")
        command = type(self)._disable_paging_command
        command = self._normalize_cmd(command)
        logger.debug(f"Host {self._host}: Disable paging command: {repr(command)}")
        self._stdin.write(command)
        output = await self._read_until_prompt()
        logger.debug(f"Host {self._host}: Disable paging output: {repr(output)}")
        if self._ansi_escape_codes:
            output = self._strip_ansi_escape_codes(output)
        return output

    async def _find_prompt(self):
        """Finds the current network device prompt, last line only"""
        logger.info(f"Host {self._host}: Finding prompt")
        self._stdin.write(self._normalize_cmd("\n"))
        prompt = ""
        delimiters = map(re.escape, type(self)._delimiter_list)
        delimiters = r"|".join(delimiters)
        prompt = await self._read_until_pattern(delimiters)
        prompt = prompt.strip()
        if self._ansi_escape_codes:
            prompt = self._strip_ansi_escape_codes(prompt)
        if not prompt:
            raise ValueError(
                f"Host {self._host}: Unable to find prompt: {repr(prompt)}"
            )
        logger.debug(f"Host {self._host}: Found Prompt: {repr(prompt)}")
        return prompt

    async def _send_command(
        self,
        command_string,
        pattern="",
        re_flags=0,
        strip_command=True,
        strip_prompt=True,
    ):
        """
        Sending command to device (support interactive commands with pattern)

        :param str command_string: command for executing basically in privilege mode
        :param str pattern: pattern for waiting in output (for interactive commands)
        :param re.flags re_flags: re flags for pattern
        :param bool strip_command: True or False for stripping command from output
        :param bool strip_prompt: True or False for stripping ending device prompt
        :return: The output of the command
        """
        logger.info(f"Host {self._host}: Sending command")
        output = ""
        command_string = self._normalize_cmd(command_string)
        logger.debug(f"Host {self._host}: Send command: {repr(command_string)}")
        self._stdin.write(command_string)
        output = await self._read_until_prompt_or_pattern(pattern, re_flags)

        # Some platforms have ansi_escape codes
        if self._ansi_escape_codes:
            output = self._strip_ansi_escape_codes(output)
        output = self._normalize_linefeeds(output)
        if strip_prompt:
            output = self._strip_prompt(output)
        if strip_command:
            output = self._strip_command(command_string, output)

        logger.debug(f"Host {self._host}: Send command output: {repr(output)}")
        return output

    async def _send_command_wrapper(self, cmd: str) -> str:
        """
        Send command to the remote device with a caching feature to
        avoid sending the same command
        twice based on the SSH_MAPPER_BASE dict cmd key.

        Parameters
        ----------
        cmd : str
            The command to send to the remote device after checking cache.

        Returns
        -------
        response : str
            The response from the remote device.
        """
        cached_results = self._results_cache.get(cmd)
        if not cached_results:
            response = await self._send_command(cmd)
            self._results_cache[cmd] = response
            return response
        else:
            return cached_results

    def _strip_prompt(self, a_string):
        """Strip the trailing router prompt from the output"""
        logger.info(f"Host {self._host}: Stripping prompt")
        response_list = a_string.split("\n")
        last_line = response_list[-1]
        if self._base_prompt in last_line:
            return "\n".join(response_list[:-1])
        else:
            return a_string

    async def _read_until_prompt(self):
        """Reads channel until self.base_pattern is detected.

        Returns all data available.
        """
        return await self._read_until_pattern(self._base_pattern)

    async def _read_until_pattern(self, pattern="", re_flags=0):
        """Reads channel until pattern detected.

        Returns all data available.
        """
        output = ""
        logger.info(f"Host {self._host}: Reading until pattern")
        if not pattern:
            pattern = self._base_pattern
        logger.debug(f"Host {self._host}: Reading pattern: {pattern}")
        while True:
            fut = self._stdout.read(self._MAX_BUFFER)
            try:
                output += await asyncio.wait_for(fut, self._timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(self._host)
            if re.search(pattern, output, flags=re_flags):
                logger.debug(
                    f"Host {self._host}: Reading pattern '{pattern}' was found:"
                    f"{repr(output)}"
                )
                return output

    async def _read_until_prompt_or_pattern(self, pattern="", re_flags=0):
        """Reads until either self.base_pattern or pattern is detected.

        Returns all data available
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
            if re.search(pattern, output, flags=re_flags) or re.search(
                base_prompt_pattern, output, flags=re_flags
            ):
                logger.debug(
                    f"Host {self._host}: Reading pattern '{pattern}' or"
                    f"'{base_prompt_pattern}' was found: {repr(output)}"
                )
                return output

    @staticmethod
    def _strip_backspaces(output):
        """Strip any backspace characters out of the output"""
        backspace_char = "\x08"
        return output.replace(backspace_char, "")

    @staticmethod
    def _strip_command(command_string, output):
        """Strips command_string from output string

        Cisco IOS adds backspaces into output for long commands
        """
        logger.info("Stripping command")
        backspace_char = "\x08"

        # Check for line wrap (remove backspaces)
        if backspace_char in output:
            output = output.replace(backspace_char, "")
            output_lines = output.split("\n")
            new_output = output_lines[1:]
            return "\n".join(new_output)
        else:
            command_length = len(command_string)
            return output[command_length:]

    @staticmethod
    def _normalize_linefeeds(a_string):
        """Convert '\r\r\n','\r\n', '\n\r' to '\n"""
        newline = re.compile(r"(\r\r\n|\r\n|\n\r)")
        return newline.sub("\n", a_string)

    @staticmethod
    def _normalize_cmd(command):
        """Normalize CLI commands to have a single trailing newline"""
        command = command.rstrip("\n")
        command += "\n"
        return command

    async def send_config_set(self, config_commands=None):
        """
        Sending configuration commands to device

        The commands will be executed one after the other.

        :param list config_commands: iterable string list with commands for applying to
        network device
        :return: The output of this commands
        """
        logger.info(f"Host {self._host}: Sending configuration settings")
        if config_commands is None:
            return ""
        if not hasattr(config_commands, "__iter__"):
            raise ValueError(
                f"Host {self._host}: Invalid argument passed into send_config_set"
            )

        # Send config commands
        logger.debug(f"Host {self._host}: Config commands: {config_commands}")
        output = ""
        for cmd in config_commands:
            self._stdin.write(self._normalize_cmd(cmd))
            output += await self._read_until_prompt()

        if self._ansi_escape_codes:
            output = self._strip_ansi_escape_codes(output)

        output = self._normalize_linefeeds(output)
        logger.debug(f"Host {self._host}: Config commands output: {repr(output)}")
        return output

    @staticmethod
    def _strip_ansi_escape_codes(string_buffer):
        """
        Remove some ANSI ESC codes from the output

        http://en.wikipedia.org/wiki/ANSI_escape_code

        Note: this does not capture ALL possible ANSI Escape Codes only the ones
        I have encountered

        Current codes that are filtered:
        ESC = '\x1b' or chr(27)
        ESC = is the escape character [^ in hex ('\x1b')
        ESC[24;27H   Position cursor
        ESC[?25h     Show the cursor
        ESC[E        Next line (HP does ESC-E)
        ESC[K        Erase line. Clear from cursor to end of screen
        ESC[2K       Erase line
        ESC[1;24r    Enable scrolling from start to row end
        ESC7         Save cursor position
        ESC[r        Scroll all screen
        ESC8         Restore cursor position
        ESC[nA       Move cursor up to n cells
        ESC[nB       Move cursor down to n cells

        require:
            HP ProCurve
            F5 LTM's
            Mikrotik
        """
        logger.info("Stripping ansi escape codes")
        logger.debug(f"Unstripped output: {repr(string_buffer)}")

        code_save_cursor = chr(27) + r"7"
        code_scroll_screen = chr(27) + r"\[r"
        code_restore_cursor = chr(27) + r"8"
        code_cursor_up = chr(27) + r"\[\d+A"
        code_cursor_down = chr(27) + r"\[\d+B"

        code_position_cursor = chr(27) + r"\[\d+;\d+H"
        code_show_cursor = chr(27) + r"\[\?25h"
        code_next_line = chr(27) + r"E"
        code_erase_line_from_cursor = chr(27) + r"\[K"
        code_erase_line = chr(27) + r"\[2K"
        code_enable_scroll = chr(27) + r"\[\d+;\d+r"

        code_set = [
            code_save_cursor,
            code_scroll_screen,
            code_restore_cursor,
            code_cursor_up,
            code_cursor_down,
            code_position_cursor,
            code_show_cursor,
            code_erase_line,
            code_erase_line_from_cursor,
            code_enable_scroll,
        ]

        output = string_buffer
        for ansi_esc_code in code_set:
            output = re.sub(ansi_esc_code, "", output)

        # CODE_NEXT_LINE must substitute with '\n'
        output = re.sub(code_next_line, "\n", output)

        logger.debug(f"Stripped output: {repr(output)}")

        return output

    async def _autodetect_std(
        self,
        cmd: str = "",
        search_patterns: Optional[List[str]] = None,
        re_flags: int = re.IGNORECASE,
        priority: int = 99,
    ) -> int:
        """
        Standard method to try to auto-detect the device type.
        This method will be called for each
        device_type present in SSH_MAPPER_BASE dict ('dispatch' key).
        It will attempt to send a command and match some regular expression
        from the ouput for each entry in SSH_MAPPER_BASE
        ('cmd' and 'search_pattern' keys).

        Parameters
        ----------
        cmd : str
            The command to send to the remote device after checking cache.
        search_patterns : list
            A list of regular expression to look for in the command's output
            (default: None).
        re_flags: re.flags, optional
            Any flags from the python re module to modify the regular expression
            (default: re.I).
        priority: int, optional
            The confidence the match is right between 0 and 99 (default: 99).
        """
        invalid_responses = [
            r"% Invalid input detected",
            r"syntax error, expecting",
            r"Error: Unrecognized command",
            r"%Error",
            r"command not found",
            r"Syntax Error: unexpected argument",
            r"% Unrecognized command found at",
        ]
        if not cmd or not search_patterns:
            return 0
        try:
            # _send_command_wrapper will use already cached results if available
            response = await self._send_command(cmd)
            # Look for error conditions in output
            for pattern in invalid_responses:
                match = re.search(pattern, response, flags=re.I)
                if match:
                    return 0
            for pattern in search_patterns:
                match = re.search(pattern, response, flags=re_flags)
                if match:
                    return priority
        except Exception:
            return 0
        return 0

    async def _cleanup(self):
        """Any needed cleanup before closing connection"""
        logger.info(f"Host {self._host}: Cleanup session")
        pass

    async def disconnect(self):
        """Gracefully close the SSH connection"""
        logger.info(f"Host {self._host}: Disconnecting")
        await self._cleanup()
        self._conn.close()
        await self._conn.wait_closed()
