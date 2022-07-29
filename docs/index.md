# Asynchronet (Under Construction)
Inspired by [Netmiko](https://github.com/ktbyers/netmiko), Asynchronet is a multi-vendor library for asynchronously interacting with network devices through the CLI.

Asynchronet is a fork of [Netdev](https://github.com/selfuryon/netdev), which is no longer maintained. This project was forked to continue to expand and enhance the existing capabilities while enabling community contribution.

The key features are:

- **Asynchronous CLI Interactions**: Thanks to [asyncssh](https://github.com/ronf/asyncssh), which powers asynchronet provides support for multiple SSH connections within a single event loop.
- **Multi-Vendor Support**: Currently twelve of the most popular networking hardware vendors are supported, with more to be added in the future.
- **Autodetect Device Type**: By porting [Netmiko's](https://github.com/ktbyers/netmiko) battle-tested [SSHDetect](https://ktbyers.github.io/netmiko/docs/netmiko/ssh_autodetect.html) class to work asynchronously with _asyncssh_, asynchronet makes automatic device type detection a breeze.
- **Simple**: Intuitive classes make it easy to interact with your favorite flavor of device.

## Requirements
Python 3.10+

## Installation

```console
$ pip install asynchronet
---> 100%
```

## Example

```python
import asyncio

import asynchronet

async def task(param):
    async with asynchronet.create(**param) as ios:
        # Send a simple command
        out = await ios.send_command("show ver")
        print(out)
        # Send a full configuration set
        commands = ["line console 0", "exit"]
        out = await ios.send_config_set(commands)
        print(out)
        # Send a command with a long output
        out = await ios.send_command("show run")
        print(out)
        # Interactive dialog
        out = await ios.send_command(
            "conf", pattern=r"\[terminal\]\?", strip_command=False
        )
        out += await ios.send_command("term", strip_command=False)
        out += await ios.send_command("exit", strip_command=False, strip_prompt=False)
        print(out)


async def run():
    device_1 = {
        "username": "user",
        "password": "pass",
        "device_type": "cisco_ios",
        "host": "ip address",
    }
    device_2 = {
        "username": "user",
        "password": "pass",
        "device_type": "cisco_ios",
        "host": "ip address",
    }
    devices = [device_1, device_2]
    tasks = [task(device) for device in devices]
    await asyncio.wait(tasks)


loop = asyncio.get_event_loop()
loop.run_until_complete(run())

```