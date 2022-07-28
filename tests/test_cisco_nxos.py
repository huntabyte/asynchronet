import asyncio
import logging
import unittest

import yaml

import asynchronet

logging.basicConfig(filename="unittest.log", level=logging.DEBUG)
asynchronet.logger.setLevel(logging.DEBUG)
config_path = "config.yaml"


class TestNXOS(unittest.TestCase):
    @staticmethod
    def load_credits():
        with open(config_path, "r") as conf:
            config = yaml.safe_load(conf)
            with open(config["device_list"], "r") as devs:
                devices = yaml.safe_load(devs)
                params = [p for p in devices if p["device_type"] == "cisco_nxos"]
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
                async with asynchronet.create(**dev) as nxos:
                    out = await nxos.send_command("show run | i hostname")
                    self.assertIn("hostname", out)

        self.loop.run_until_complete(task())

    def test_timeout(self):
        async def task():
            for dev in self.devices:
                with self.assertRaises(asynchronet.TimeoutError):
                    async with asynchronet.create(**dev, timeout=0.1) as nxos:
                        await nxos.send_command("show run | i hostname")

        self.loop.run_until_complete(task())

    def test_show_several_commands(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as nxos:
                    commands = ["dir", "show ver", "show run", "show ssh key"]
                    for cmd in commands:
                        out = await nxos.send_command(cmd, strip_command=False)
                        self.assertIn(cmd, out)

        self.loop.run_until_complete(task())

    def test_config_set(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as nxos:
                    commands = ["line con", "exit"]
                    out = await nxos.send_config_set(commands)
                    self.assertIn("line con", out)
                    self.assertIn("exit", out)

        self.loop.run_until_complete(task())

    def test_base_prompt(self):
        async def task():
            for dev in self.devices:
                async with asynchronet.create(**dev) as nxos:
                    out = await nxos.send_command("sh run | i hostname")
                    self.assertIn(nxos.base_prompt, out)

        self.loop.run_until_complete(task())
