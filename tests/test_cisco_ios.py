import asyncio
import logging
import unittest

import yaml

import asynchronet

logging.basicConfig(filename="unittest.log", level=logging.DEBUG)
config_path = "config.yaml"


class TestIOS(unittest.TestCase):
    @staticmethod
    def load_credits():
        with open(config_path, "r") as conf:
            config = yaml.safe_load(conf)
            with open(config["device_list"], "r") as devs:
                devices = yaml.safe_load(devs)
                params = [p for p in devices if p["device_type"] == "cisco_ios"]
                return params

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_debug(False)
        asyncio.set_event_loop(self.loop)
        self.devices = self.load_credits()
        self.assertFalse(len(self.devices) == 0)

    def test_show_run_hostname(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as ios:
                    out = await ios.send_command("show run | i hostname")
                    self.assertIn("hostname", out)

        self.loop.run_until_complete(task())

    def test_timeout(self):
        async def task():
            for dev in self.devices:
                with self.assertRaises(asynchronet.TimeoutError):
                    async with asynchronet.create(**dev, timeout=0.1) as ios:
                        await ios.send_command("show run | i hostname")

        self.loop.run_until_complete(task())

    def test_show_several_commands(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as ios:
                    commands = ["dir", "show ver", "show run", "show ssh"]
                    for cmd in commands:
                        out = await ios.send_command(cmd, strip_command=False)
                        self.assertIn(cmd, out)

        self.loop.run_until_complete(task())

    def test_config_set(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as ios:
                    commands = ["line con 0", "exit"]
                    out = await ios.send_config_set(commands)
                    self.assertIn("line con 0", out)
                    self.assertIn("exit", out)

        self.loop.run_until_complete(task())

    def test_base_prompt(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as ios:
                    out = await ios.send_command("sh run | i hostname")
                    self.assertIn(ios.base_prompt, out)

        self.loop.run_until_complete(task())

    def test_interactive_commands(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as ios:
                    out = await ios.send_command(
                        "conf", pattern=r"\[terminal\]\?", strip_command=False
                    )
                    out += await ios.send_command("term", strip_command=False)
                    out += await ios.send_command("exit", strip_command=False)
                    self.assertIn("Enter configuration commands", out)

        self.loop.run_until_complete(task())
