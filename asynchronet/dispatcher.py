"""Contains the factory function which generates asynhcronet device objects.

"""
from asynchronet.vendors import AlcatelAOS
from asynchronet.vendors import AristaEOS
from asynchronet.vendors import ArubaAOS6, ArubaAOS8
from asynchronet.vendors import CiscoASA, CiscoIOS, CiscoIOSXR, CiscoNXOS, CiscoSG3XX
from asynchronet.vendors import FujitsuSwitch
from asynchronet.vendors import HPComware, HPComwareLimited
from asynchronet.vendors import JuniperJunOS
from asynchronet.vendors import MikrotikRouterOS
from asynchronet.vendors import Terminal
from asynchronet.vendors import UbiquityEdgeSwitch
from asynchronet.vendors import HW1000
from asynchronet.vendors import Huawei

# @formatter:off
# The keys of this dictionary are the supported device_types
CLASS_MAPPER = {
    "alcatel_aos": AlcatelAOS,
    "arista_eos": AristaEOS,
    "aruba_aos_6": ArubaAOS6,
    "aruba_aos_8": ArubaAOS8,
    "cisco_asa": CiscoASA,
    "cisco_ios": CiscoIOS,
    "cisco_ios_xe": CiscoIOS,
    "cisco_ios_xr": CiscoIOSXR,
    "cisco_nxos": CiscoNXOS,
    "cisco_sg3xx": CiscoSG3XX,
    "fujitsu_switch": FujitsuSwitch,
    "hp_comware": HPComware,
    "hp_comware_limited": HPComwareLimited,
    "juniper_junos": JuniperJunOS,
    "mikrotik_routeros": MikrotikRouterOS,
    "ubiquity_edge": UbiquityEdgeSwitch,
    "terminal": Terminal,
    "hw1000": HW1000,
    "huawei": Huawei,
}

# @formatter:on

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_str = "\n".join(platforms)


def create(*args, **kwargs):
    """Selects the proper vendor and creates an object based on device_type

    Selects the proper class and creates a device object based on
    the device_type argument.

    Other parameters:
        **host: device hostname or ip address for connection
        **username: username for logging to device
        **password: user password for logging to device
        **port: ssh port for connection. Default is 22
        **device_type: network device type
        **timeout: timeout in second for getting information from channel
        **loop: asyncio loop object
        **known_hosts: file with known hosts. Default is None (no policy).
            With () it will use default file
        **local_addr: local address for binding source of tcp connection
        **client_keys: path for client keys. Default in None.
            With () it will use default file in OS
        **passphrase: password for encrypted client keys
        **tunnel: An existing SSH connection that this new connection
            should be tunneled over
        **pattern: pattern for searching the end of device prompt.
                Example: r"{hostname}.*?(\(.*?\))?[{delimeters}]"
        **agent_forwarding: Allow or not allow agent forward for server
        **agent_path:
            The path of a UNIX domain socket to use to contact an ssh-agent
            process which will perform the operations needed for client
            public key authentication. If this is not specified and the environment
            variable `SSH_AUTH_SOCK` is set, its value will be used as the path.
            If `client_keys` is specified or this argument is explicitly set to `None`,
            an ssh-agent will not be used.
        **client_version: version which advertised to ssh server
        **family:
           The address family to use when creating the socket. By default,
           the address family is automatically selected based on the host.
        **kex_algs:
            A list of allowed key exchange algorithms in the SSH handshake,
            taken from `key exchange algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#kexalgs>`_
        **encryption_algs:
            A list of encryption algorithms to use during the SSH handshake,
            taken from `encryption algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#encryptionalgs>`_
        **mac_algs:
            A list of MAC algorithms to use during the SSH handshake, taken
            from `MAC algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#macalgs>`_
        **compression_algs:
            A list of compression algorithms to use during the SSH handshake,
            taken from `compression algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#compressionalgs>`_, or
            `None` to disable compression
        **signature_algs:
            A list of public key signature algorithms to use during the SSH
            handshake, taken from `signature algorithms
            <https://asyncssh.readthedocs.io/en/latest/api.html#signaturealgs>`_
        **server_host_key_algs:
            A list of server host key algorithms to allow during the SSH handshake,
            taken from server host key algorithms.
            https://asyncssh.readthedocs.io/en/latest/api.html#publickeyalgs

    """
    if kwargs["device_type"] not in platforms:
        raise ValueError(
            f"Unsupported device_type: "
            f"currently supported platforms are: {platforms_str}"
        )
    connection_class = CLASS_MAPPER[kwargs["device_type"]]
    return connection_class(*args, **kwargs)
