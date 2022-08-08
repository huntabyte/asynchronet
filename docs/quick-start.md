## Create Device Inventory

Create a simple dictionary representing the device you plan to manage.
```python
import asyncio

import asynchronet

devices = [
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.101",
        "username": "admin",
        "password": "password",
    },
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.102",
        "username": "admin",
        "password": "password",
    },
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.103",
        "username": "admin",
        "password": "password",
    },
]
```

## Define a Task
```python
async def get_version(device):
    async with asynchronet.create(**device) as ios:
        # Send a simple command
        result = await ios.send_command("show version")
        print(result)
```

## Schedule Calls
```python
async def main():
    results = await asyncio.gather(
        *[get_version(device) for device in devices]
    )
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## Full Example
Your full file should now look like this
```python
# main.py

import asyncio

import asynchronet

devices = [
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.101",
        "username": "admin",
        "password": "password",
    },
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.102",
        "username": "admin",
        "password": "password",
    },
    {
        "device_type": "cisco_ios",
        "host": "10.199.199.103",
        "username": "admin",
        "password": "password",
    },
]

async def get_version(device):
    async with asynchronet.create(**device) as ios:
        # Send a simple command
        result = await ios.send_command("show version")
        print(result)

async def main():
    results = await asyncio.gather(
        *[get_version(device) for device in devices]
    )
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run
```console
python main.py
```
