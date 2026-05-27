# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Miscellaneous utility functions."""

from __future__ import annotations

import functools
import importlib.resources as pkg_resources
import io
import os
import re
import sys
from datetime import datetime
from glob import glob
from typing import TYPE_CHECKING
from typing import Any
from typing import AnyStr
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union
from typing import cast

# For decorators
F = TypeVar("F", bound=Callable[..., Any])


if TYPE_CHECKING:
    from os import PathLike

    from htmiko.base_connection import BaseConnection

try:
    import serial.tools.list_ports

    PYSERIAL_INSTALLED = True
except ImportError:
    PYSERIAL_INSTALLED = False

# Dictionary mapping 'show run' for vendors with different command
SHOW_RUN_MAPPER = {
    "brocade_fos": "configShow",
    "juniper": "show configuration",
    "juniper_junos": "show configuration",
    "extreme": "show configuration",
    "extreme_ers": "show running-config",
    "extreme_exos": "show configuration",
    "extreme_netiron": "show running-config",
    "extreme_nos": "show running-config",
    "extreme_slx": "show running-config",
    "extreme_vdx": "show running-config",
    "extreme_vsp": "show running-config",
    "extreme_wing": "show running-config",
    "ericsson_ipos": "show configuration",
    "hp_comware": "display current-configuration",
    "huawei": "display current-configuration",
    "fortinet": "show full-configuration",
    "checkpoint": "show configuration",
    "cisco_wlc": "show run-config",
    "enterasys": "show running-config",
    "dell_force10": "show running-config",
    "avaya_vsp": "show running-config",
    "avaya_ers": "show running-config",
    "brocade_vdx": "show running-config",
    "brocade_nos": "show running-config",
    "brocade_fastiron": "show running-config",
    "brocade_netiron": "show running-config",
    "alcatel_aos": "show configuration snapshot",
    "cros_mtbr": "show running-config",
}

# Expand SHOW_RUN_MAPPER to include '_ssh' key
new_dict = {}
for k, v in SHOW_RUN_MAPPER.items():
    new_key = k + "_ssh"
    new_dict[k] = v
    new_dict[new_key] = v
SHOW_RUN_MAPPER = new_dict

# Default location of htmiko temp directory for htmiko tools
HTMIKO_BASE_DIR = "~/.htmiko"


def load_yaml_file(yaml_file: Union[str, bytes, "PathLike[Any]"]) -> Any:
    """Read YAML file."""
    try:
        import yaml
    except ImportError:
        sys.exit("Unable to import yaml module.")
    try:
        with io.open(yaml_file, "rt", encoding="utf-8") as fname:
            return yaml.safe_load(fname)
    except IOError:
        sys.exit("Unable to open YAML file")


def load_htmiko_yml(file_name: Union[str, bytes, "PathLike[Any]", None] = None) -> Any:
    """
    Load and parse the .htmiko.yml as determined by 'find_cfg_file'.

    Parsing:
        Retrieve and extract 'config' parameters: __meta__ field
        Determine if encryption is being used and decrypt any encrypted fields
    """
    yaml_devices_file = find_cfg_file(file_name)
    htmiko_yaml_data = load_yaml_file(yaml_devices_file)
    config_params = htmiko_yaml_data.pop("__meta__", {})
    return config_params, htmiko_yaml_data


def load_devices(file_name: Union[str, bytes, "PathLike[Any]", None] = None) -> Any:
    """Find and load .htmiko.yml file."""
    yaml_devices_file = find_cfg_file(file_name)
    return load_yaml_file(yaml_devices_file)


def find_cfg_file(
    file_name: Union[str, bytes, "PathLike[Any]", None] = None,
) -> Union[str, bytes, "PathLike[Any]"]:
    """
    Search for htmiko_tools inventory file in the following order:
    HTMIKO_TOOLS_CFG environment variable
    Current directory
    Home directory
    Look for file named: .htmiko.yml or htmiko.yml
    Also allow HTMIKO_TOOLS_CFG to point directly at a file
    """
    if file_name and os.path.isfile(file_name):
        return file_name
    optional_path = os.environ.get("HTMIKO_TOOLS_CFG", "")
    if os.path.isfile(optional_path):
        return optional_path
    search_paths = [optional_path, ".", os.path.expanduser("~")]
    # Filter optional_path if null
    search_paths = [path for path in search_paths if path]
    for path in search_paths:
        files = glob(f"{path}/.htmiko.yml") + glob(f"{path}/htmiko.yml")
        if files:
            return files[0]
    raise IOError(
        ".htmiko.yml file not found in HTMIKO_TOOLS_CFG environment variable directory,"
        " current directory, or home directory.",
    )


def display_inventory(my_devices: Dict[str, Union[List[str], Dict[str, Any]]]) -> None:
    """Print out inventory devices and groups."""
    config_params = my_devices.pop("__meta__", {})  # noqa
    inventory_groups = ["all"]
    inventory_devices = []
    for k, v in my_devices.items():
        if isinstance(v, list):
            inventory_groups.append(k)
        elif isinstance(v, dict):
            inventory_devices.append((k, v["device_type"]))

    inventory_groups.sort()
    inventory_devices.sort(key=lambda x: x[0])
    print("\nDevices:")
    print("-" * 40)
    for a_device, device_type in inventory_devices:
        device_type = f"  ({device_type})"
        print(f"{a_device:<25}{device_type:>15}")
    print("\n\nGroups:")
    print("-" * 40)
    for a_group in inventory_groups:
        print(a_group)
    print()


def obtain_all_devices(
    my_devices: Dict[str, Union[List[str], Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    """Dynamically create 'all' group."""
    new_devices = {}
    for device_name, device_or_group in my_devices.items():
        # Skip any groups
        if not isinstance(device_or_group, list):
            new_devices[device_name] = device_or_group
    return new_devices


def obtain_htmiko_filename(device_name: str) -> str:
    """Create file name based on device_name."""
    _, htmiko_full_dir = find_htmiko_dir()
    return f"{htmiko_full_dir}/{device_name}.txt"


def write_tmp_file(device_name: str, output: str) -> str:
    file_name = obtain_htmiko_filename(device_name)
    with open(file_name, "w") as f:
        f.write(output)
    return file_name


def ensure_dir_exists(verify_dir: str) -> None:
    """Ensure directory exists. Create if necessary."""
    if not os.path.exists(verify_dir):
        # Doesn't exist create dir
        os.makedirs(verify_dir)
    else:
        # Exists
        if not os.path.isdir(verify_dir):
            # Not a dir, raise an exception
            raise ValueError(f"{verify_dir} is not a directory")


def find_htmiko_dir() -> Tuple[str, str]:
    """Check environment first, then default dir"""
    try:
        htmiko_base_dir = os.environ["HTMIKO_DIR"]
    except KeyError:
        htmiko_base_dir = HTMIKO_BASE_DIR
    htmiko_base_dir = os.path.expanduser(htmiko_base_dir)
    if htmiko_base_dir == "/":
        raise ValueError("/ cannot be htmiko_base_dir")
    htmiko_full_dir = f"{htmiko_base_dir}/tmp"
    return (htmiko_base_dir, htmiko_full_dir)


def write_bytes(out_data: AnyStr, encoding: str = "utf-8") -> bytes:
    """Ensure output is properly encoded bytes."""
    if isinstance(out_data, str):
        return out_data.encode(encoding)
    elif isinstance(out_data, bytes):
        return out_data
    msg = f"Invalid value for out_data neither unicode nor byte string: {str(out_data)}"
    raise ValueError(msg)


def check_serial_port(name: str) -> str:
    """returns valid COM Port."""

    if not PYSERIAL_INSTALLED:
        msg = "\npyserial is not installed. Please PIP install pyserial:\n\npip install pyserial\n\n"
        raise ValueError(msg)

    try:
        cdc = next(serial.tools.list_ports.grep(name))
        serial_port = cdc[0]
        assert isinstance(serial_port, str)
        return serial_port
    except StopIteration:
        msg = f"device {name} not found. "
        msg += "available devices are: "
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            msg += f"{str(p)},"
        raise ValueError(msg)


def get_template_dir(_skip_ntc_package: bool = False) -> str:
    """
    Find and return the directory containing the TextFSM index file.

    Order of preference is:
    1) Find directory in `NET_TEXTFSM` Environment Variable.
    2) Check for pip installed `ntc-templates` location in this environment.
    3) ~/ntc-templates/ntc_templates/templates.

    If `index` file is not found in any of these locations, raise ValueError

    :return: directory containing the TextFSM index file

    """

    msg = """
Directory containing TextFSM index file not found.

Please set the NET_TEXTFSM environment variable to point at the directory containing your TextFSM
index file.

Alternatively, `pip install ntc-templates` (if using ntc-templates).

"""

    # Try NET_TEXTFSM environment variable
    template_dir = os.environ.get("NET_TEXTFSM")
    if template_dir is not None:
        template_dir = os.path.expanduser(template_dir)
        index = os.path.join(template_dir, "index")
        if not os.path.isfile(index):
            # Assume only base ./ntc-templates specified
            template_dir = os.path.join(template_dir, "templates")

    else:
        # Try 'pip installed' ntc-templates
        try:
            # New API for Python 3.13+
            if sys.version_info >= (3, 13):
                with pkg_resources.path("ntc_templates", "parse.py") as posix_path:
                    # Example: /venv/htmiko/lib/python3.13/site-packages/ntc_templates/templates
                    template_dir = str(posix_path.parent.joinpath("templates"))
                    # This is for automated testing
                    if _skip_ntc_package:
                        raise ModuleNotFoundError()
            else:
                with pkg_resources.path(
                    package="ntc_templates",
                    resource="parse.py",
                ) as posix_path:
                    # Example: /opt/venv/htmiko/lib/python3.9/site-packages/ntc_templates/templates
                    template_dir = str(posix_path.parent.joinpath("templates"))
                    # This is for automated testing
                    if _skip_ntc_package:
                        raise ModuleNotFoundError()
        except ModuleNotFoundError:
            # Finally check in ~/ntc-templates/ntc_templates/templates
            home_dir = os.path.expanduser("~")
            template_dir = os.path.join(
                home_dir,
                "ntc-templates",
                "ntc_templates",
                "templates",
            )

    index = os.path.join(template_dir, "index")
    if not os.path.isdir(template_dir) or not os.path.isfile(index):
        raise ValueError(msg)
    return os.path.abspath(template_dir)


def select_cmd_verify(func: F) -> F:
    """Override function cmd_verify argument with global setting."""

    @functools.wraps(func)
    def wrapper_decorator(self: "BaseConnection", *args: Any, **kwargs: Any) -> Any:
        if self.global_cmd_verify is not None:
            kwargs["cmd_verify"] = self.global_cmd_verify
        return func(self, *args, **kwargs)

    return cast(F, wrapper_decorator)


def m_exec_time(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(self: Any, *args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        result = func(self, *args, **kwargs)
        end_time = datetime.now()
        method_name = str(func)
        print(f"{method_name}: Elapsed time: {end_time - start_time}")
        return result

    return cast(F, wrapper_decorator)


def f_exec_time(func: F) -> F:
    @functools.wraps(func)
    def wrapper_decorator(*args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"Elapsed time: {end_time - start_time}")
        return result

    return cast(F, wrapper_decorator)


def nokia_context_filter(data: str, re_flags: int = re.M) -> str:
    """
    Nokia context from string. Examples:

    (ro)[]

    (ex)[configure router "Base" bgp]

    Converted over to a standalone function for easier unit testing.
    """
    context_pattern = r"^\!?\*?(\((ex|gl|pr|ro)\))?\[.*\]"
    return re.sub(context_pattern, "", data, flags=re_flags)
