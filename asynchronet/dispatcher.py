"""
Factory function for creating asynchronet classes using `device_type`
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
    """
    Factory function selects the proper class and creates object
    based on device_type
    """
    if kwargs["device_type"] not in platforms:
        raise ValueError(
            f"Unsupported device_type: "
            f"currently supported platforms are: {platforms_str}"
        )
    connection_class = CLASS_MAPPER[kwargs["device_type"]]
    return connection_class(*args, **kwargs)
