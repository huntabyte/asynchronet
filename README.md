# Asynchronet
Asynchronet is a fork of [Netdev](https://github.com/selfuryon/netdev), which is no longer maintained.

Inspired by [Netmiko](https://github.com/ktbyers/netmiko), Asynchronet is a multi-vendor library for asynchronously interacting with network devices through the CLI.

This project was forked to continue to expand and enhance the existing capabilities while enabling community contribution.

### New Capabilities
- Autodetect devices asynchronously, using an asynchronous port of [Netmiko](https://github.com/ktbyers/netmiko)'s AutoDetect functionality.

## Requirements:
* Python >=3.9

## 🚀Installation
You can install `asynchronet` using pip
```
pip install asynchronet
```

## Basic Usage
interacting with Cisco IOS devices

```python
    import asyncio
    import netdev

    async def task(param):
        async with netdev.create(**param) as ios:
            # Testing sending simple command
            out = await ios.send_command("show ver")
            print(out)
            # Testing sending configuration set
            commands = ["line console 0", "exit"]
            out = await ios.send_config_set(commands)
            print(out)
            # Testing sending simple command with long output
            out = await ios.send_command("show run")
            print(out)
            # Testing interactive dialog
            out = await ios.send_command("conf", pattern=r'\[terminal\]\?', strip_command=False)
            out += await ios.send_command("term", strip_command=False)
            out += await ios.send_command("exit", strip_command=False, strip_prompt=False)
            print(out)


    async def run():
        dev1 = { 'username' : 'user',
                 'password' : 'pass',
                 'device_type': 'cisco_ios',
                 'host': 'ip address',
        }
        dev2 = { 'username' : 'user',
                 'password' : 'pass',
                 'device_type': 'cisco_ios',
                 'host': 'ip address',
        }
        devices = [dev1, dev2]
        tasks = [task(dev) for dev in devices]
        await asyncio.wait(tasks)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
```


## Currently Supports:
- Cisco IOS 
- Cisco IOS XE
- Cisco IOS XR
- Cisco ASA
- Cisco NX-OS
- Cisco SG3XX
- HP Comware (like V1910 too)
- Fujitsu Blade Switches
- Mikrotik RouterOS
- Arista EOS
- Juniper JunOS
- Aruba AOS 6.X
- Aruba AOS 8.X
- Terminal
- Alcatel AOS
