"""
Vipnet HW1000  support

For use with Vipnet HW1000 Crypto Gateways

"""

import re
from asynchronet.logger import logger
from asynchronet.vendors.base import BaseDevice


class HW1000(BaseDevice):
    """
    Class for interacting with Vipnet HW1000 crypto gateways

    HW1000 devices have three administration modes:
    *user exec or unprivileged exec. This mode allows you perform basic tests &
        get system information.
    *privilege exec. This mode allows all EXEC mode commands available on the system.
        HW100 supports only one active privilege session. Use preempt_privilege=True
        to close current privilege session
    *shell. This mode exits standart device shell and enters Linux shell
    """

    def __init__(self, secret="", preempt_privilege=False, *args, **kwargs):
        """
        Initialize class for asynchronous working with network devices
        :param str host: device hostname or ip address for connection
        :param str username: username for logging to device
        :param str password: user password for logging to device
        :param str secret: secret password for privilege mode
        :param bool preempt_privilege: close current privilige session (if exists).
            (default=False)
        :param int port: ssh port for connection.
            (default=22)
        :param str device_type: network device type
        :param known_hosts: file with known hosts.
            (default=None) With () it will use default file
        :param str local_addr: local address for binding source of tcp connection
        :param client_keys: path for client keys.
            (default=None) With () it will use default file in OS
        :param str passphrase: password for encrypted client keys
        :param float timeout: timeout in second for getting information from channel
        :param loop: asyncio loop object
        """
        self._secret = secret
        self._preempt_privilege = preempt_privilege

        super().__init__(*args, **kwargs)

    # Command to enter privilege exec mode
    _priv_enter = "enable"

    # Command to exist privilege exec to user exec mode
    _priv_exit = "exit"

    # String to check in prompt - if exists - we're in privilege exec mode
    _priv_check = "#"

    # Confirmation message for privilege preemption
    _priv_confirm_message = (
        "Are you sure you want to force termination of the specified session"
    )

    # Comamnd to enter Linux shell
    _shell_enter = "admin esc"

    # Command to exist Linux shell
    _shell_exit = "exit"

    # String to check in prompt - if exit's - we're in linux shell
    _shell_check = "sh"

    # Confirmation message for entering Linux shell
    _shell_enter_message = "Are you sure you want to exit to the Linux system shell?"

    async def connect(self):
        """
        Basic asynchronous connection method for HW1000 devices

        It connects to device and makes some preparation steps for working.
        Usual using 3 functions:

        * _establish_connection() for connecting to device
        * _set_base_prompt() for finding and setting device prompt
        * _enable() for getting privilege exec mode
        """
        logger.info(f"Host {self._host}: Trying to connect to the device")
        await self._establish_connection()
        await self._set_base_prompt()
        await self.enable_mode()
        logger.info(f"Host {self._host}: Has connected to the device")

    async def check_enable_mode(self):
        """Check if we are in privilege exec. Return boolean"""
        logger.info(f"Host {self._host}: Checking privilege exec")
        check_string = type(self)._priv_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_prompt()
        return check_string in output

    async def enable_mode(self, pattern="password", re_flags=re.IGNORECASE):
        """Enter to privilege exec"""
        logger.info(f"Host {self._host}: Entering to privilege exec")
        output = ""
        enable_command = type(self)._priv_enter
        if not await self.check_enable_mode():
            self._stdin.write(self._normalize_cmd(enable_command))
            output += await self._read_until_prompt_or_pattern(
                pattern=pattern, re_flags=re_flags
            )
            if re.search(pattern, output, re_flags):
                self._stdin.write(self._normalize_cmd(self._secret))
                output += await self._read_until_prompt_or_pattern(
                    pattern=type(self)._priv_confirm_message, re_flags=re_flags
                )
                if re.search(type(self)._priv_confirm_message, output, re_flags):
                    if self._preempt_privilege:
                        self._stdin.write(self._normalize_cmd("Yes"))
                    else:
                        raise ValueError(
                            "Failed to enter privilege exec:"
                            "there is already a active administration session."
                            "Use preempt_privilege=True"
                        )
            if not await self.check_enable_mode():
                raise ValueError("Failed to enter to privilege exec")
        return output

    async def exit_enable_mode(self):
        """Exit from privilege exec"""
        logger.info(f"Host {self._host}: Exiting from privilege exec")
        output = ""
        exit_enable = type(self)._priv_exit
        if await self.check_enable_mode():
            self._stdin.write(self._normalize_cmd(exit_enable))
            output += await self._read_until_prompt()
            if await self.check_enable_mode():
                raise ValueError("Failed to exit from privilege exec")
        return output

    async def check_shell_mode(self):
        """Checks if device in shell mode or not"""
        logger.info(f"Host {self._host}: Checking shell mode")
        check_string = type(self)._shell_check
        self._stdin.write(self._normalize_cmd("\n"))
        output = await self._read_until_pattern(r"[\>|\#]")
        logger.info(output)
        return check_string in output

    async def enter_shell_mode(self, re_flags=re.IGNORECASE):
        """Enter into shell mode"""
        logger.info(f"Host {self._host}: Entering to shell mode")
        output = ""
        shell_command = type(self)._shell_enter
        if not await self.check_shell_mode():
            self._stdin.write(self._normalize_cmd(shell_command))
            output += await self._read_until_pattern(
                pattern=type(self)._shell_enter_message, re_flags=re_flags
            )
            self._stdin.write(self._normalize_cmd("Yes"))
            output += await self._read_until_pattern("password:", re_flags=re_flags)
            self._stdin.write(self._normalize_cmd(self._secret))
            output += await self._read_until_pattern(r"[\>|\#]")
            await self._set_base_prompt()  # base promt differs in shell mode
            if not await self.check_shell_mode():
                raise ValueError("Failed to enter to shell mode")
        return output

    async def exit_shell_mode(self):
        """Exit from shell mode"""
        logger.info(f"Host {self._host}: Exiting from shell mode")
        output = ""
        exit_shell = type(self)._shell_exit
        if await self.check_shell_mode():
            self._stdin.write(self._normalize_cmd(exit_shell))
            output = await self._read_until_pattern(r"[\>|\#]")
            if await self.check_shell_mode():
                raise ValueError("Failed to exit from shell mode")
            await self._set_base_prompt()  # base promt differs in shell mode
        return output

    async def _cleanup(self):
        """Any needed cleanup before closing connection"""
        logger.info(f"Host {self._host}: Cleanup session")
        await self.exit_shell_mode()
        await self.exit_enable_mode()
