import asyncio
from asynchronet.vendors.autodetect import SSHDetect


devices = [
    {
        "device_type": "autodetect",
        "host": "10.199.199.101",
        "username": "admin",
        "password": "admin",
    },
    {
        "device_type": "autodetect",
        "host": "10.199.199.102",
        "username": "admin",
        "password": "admin",
    },
    {
        "device_type": "autodetect",
        "host": "10.199.199.103",
        "username": "admin",
        "password": "admin",
    },
]


async def guess(device):
    guesser = SSHDetect(**device)
    best_match = await guesser.autodetect()
    print(best_match)
    return best_match


async def main():
    results = await asyncio.gather(*[guess(device) for device in devices])
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
