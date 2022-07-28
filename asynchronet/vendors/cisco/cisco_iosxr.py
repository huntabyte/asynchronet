from asynchronet.exceptions import CommitError
from asynchronet.logger import logger
from asynchronet.vendors.ios_like import IOSLikeDevice


class CiscoIOSXR(IOSLikeDevice):
    """Class for working with Cisco IOS XR"""

    # Command to commit changes
    _commit_command = "commit"
    """Command for committing changes"""

    # Command to commit changes with a comment
    _commit_comment_command = "commit comment {}"
    """Command for committing changes with comment"""

    # Command to abort changes and exit to privilege mode
    _abort_command = "abort"

    # Command to show failed commit reason
    _show_config_failed = "show configuration failed"

    # Command to show other commits which occurred during the session
    _show_commit_changes = "show configuration commit changes"

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
            to network device in system view
        :param bool with_commit: if True, commit all changes after
            applying config_commands
        :param string commit_comment: message for configuration commit
        :param bool exit_config_mode: if True, automatically quit configuration mode
        :return: The output of these commands
        """

        if config_commands is None:
            return ""

        # Send config commands
        output = await self.config_mode()
        output += await super(IOSLikeDevice, self).send_config_set(
            config_commands=config_commands
        )
        if with_commit:
            commit = type(self)._commit_command
            if commit_comment:
                commit = type(self)._commit_comment_command.format(commit_comment)

            self._stdin.write(self._normalize_cmd(commit))
            output += await self._read_until_prompt_or_pattern(
                r"Do you wish to proceed with this commit anyway\?"
            )
            if "Failed to commit" in output:
                show_config_failed = type(self)._show_config_failed
                reason = await self.send_command(
                    self._normalize_cmd(show_config_failed)
                )
                raise CommitError(self._host, reason)
            if "One or more commits have occurred" in output:
                show_commit_changes = type(self)._show_commit_changes
                self._stdin.write(self._normalize_cmd("no"))
                reason = await self.send_command(
                    self._normalize_cmd(show_commit_changes)
                )
                raise CommitError(self._host, reason)

        if exit_config_mode:
            output += await self.exit_config_mode()

        output = self._normalize_linefeeds(output)
        logger.debug(f"Host {self._host}: Config commands output: {repr(output)}")
        return output

    async def exit_config_mode(self):
        """Exits from configuration mode"""
        logger.info(f"Host {self._host}: Exiting from configuration mode")
        output = ""
        exit_config = type(self)._config_exit
        if await self.check_config_mode():
            self._stdin.write(self._normalize_cmd(exit_config))
            output = await self._read_until_prompt_or_pattern(
                r"Uncommitted changes found"
            )
            if "Uncommitted changes found" in output:
                self._stdin.write(self._normalize_cmd("no"))
                output += await self._read_until_prompt()
            if await self.check_config_mode():
                raise ValueError("Failed to exit from configuration mode")
        return output

    async def _cleanup(self):
        """Any needed cleanup before closing connection"""
        abort = type(self)._abort_command
        abort = self._normalize_cmd(abort)
        self._stdin.write(abort)
        logger.info(f"Host {self._host}: Cleanup session")
