# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech


from __future__ import annotations

import csv
import functools
import os
import time
from datetime import datetime

import network_utilities
import pytest
import yaml
from perf_utils import commands

from htmiko import ConnectHandler
from htmiko import __version__

# import logging
# logging.basicConfig(filename='test.log', level=logging.DEBUG)
# logger = logging.getLogger("htmiko")

PRINT_DEBUG = False


def generate_csv_timestamp():
    """yyyy-MM-dd HH:mm:ss"""
    now = datetime.now()
    t_stamp = f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}"
    return t_stamp


def write_csv(device_name, htmiko_results):
    results_file = "htmiko_performance.csv"
    file_exists = os.path.isfile(results_file)
    with open(results_file, "a") as csv_file:
        field_names = ["date", "htmiko_version", "device_name"] + list(
            htmiko_results.keys(),
        )
        t_stamp = generate_csv_timestamp()
        csv_write = csv.DictWriter(csv_file, fieldnames=field_names)

        # Write the header only once
        if not file_exists:
            csv_write.writeheader()

        entry = {
            "date": t_stamp,
            "htmiko_version": __version__,
            "device_name": device_name,
        }

        for func_name, exec_time in htmiko_results.items():
            entry[func_name] = exec_time
        csv_write.writerow(entry)


def f_exec_time(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        time_delta = end_time - start_time
        print(f"{str(func)}: Elapsed time: {time_delta}")
        return (time_delta, result)

    return wrapper_decorator


def read_devices():
    f_name = os.environ.get("TEST_DEVICES", "test_devices.yml")
    with open(f_name) as f:
        return yaml.safe_load(f)


@f_exec_time
def connect(device):
    with ConnectHandler(**device) as conn:
        prompt = conn.find_prompt()
        PRINT_DEBUG and print(prompt)


@f_exec_time
def send_command_simple(device):
    with ConnectHandler(**device) as conn:
        platform = device["device_type"]
        cmd = commands(platform)["basic"]
        output = conn.send_command(cmd)
        PRINT_DEBUG and print(output)


@f_exec_time
def save_config(device):
    platform = device["device_type"]
    if "cisco_xr" in platform or "juniper" in platform:
        return
    with ConnectHandler(**device) as conn:
        platform = device["device_type"]
        output = conn.save_config()
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_simple(device):
    with ConnectHandler(**device) as conn:
        platform = device["device_type"]
        cmd = commands(platform)["config"][0]
        output = conn.send_config_set(cmd)
        PRINT_DEBUG and print(output)


@f_exec_time
def send_config_large_acl(device):

    # Results will be marginally distorted by generating the ACL here.
    device_type = device["device_type"]
    func_name = f"generate_{device_type}_acl"
    func = getattr(network_utilities, func_name)

    with ConnectHandler(**device) as conn:
        cfg = func(entries=100)
        output = conn.send_config_set(cfg)
        PRINT_DEBUG and print(output)


@f_exec_time
def cleanup(device):

    # Results will be marginally distorted by generating the ACL here.
    platform = device["device_type"]
    if "juniper_junos" in platform:
        remove_acl_cmd = "rollback 0"
    elif "hp_procurve" in platform:
        remove_acl_cmd = None
    elif "cisco_asa" in platform:
        remove_acl_cmd = "clear configure access-list htmiko_test_large_acl"
    elif "linux" in platform:
        # Do nothing i.e. no cleanup
        return
    else:
        base_acl_cmd = commands(platform)["config_long_acl"]["base_cmd"]
        remove_acl_cmd = f"no {base_acl_cmd}"
    cleanup_generic(device, remove_acl_cmd)


def cleanup_generic(device, command):
    if command is None:
        return
    with ConnectHandler(**device) as conn:
        output = conn.send_config_set(command)
        PRINT_DEBUG and print(output)


def remove_old_data(device_name):
    results_file = "htmiko_performance.csv"
    entries = []
    try:
        with open(results_file) as f:
            read_csv = csv.DictReader(f)
            for entry in read_csv:
                entry = dict(entry)
                version, device = entry["htmiko_version"], entry["device_name"]
                if (
                    version != __version__ and device == device_name
                ) or device_name != device:
                    entries.append(entry)
    except FileNotFoundError:
        print(r"{results_file} does not exist.  creating")

    with open(results_file, "w", newline="") as csv_file:
        if entries:
            field_names = list(entries[0].keys())
            csv_write = csv.DictWriter(csv_file, fieldnames=field_names)
            csv_write.writeheader()
            csv_write.writerows(entries)
        else:
            print(r"{results_file} would be empty.  skipping")


def main():
    PASSWORD = os.environ.get("HTMIKO_PASSWORD", "NOT SET")
    HP_PASSWORD = os.environ.get("HPE_PASSWORD", "NOT SET")

    devices = read_devices()
    print("\n\n")
    for dev_name, params in devices.items():
        remove_old_data(dev_name)
        dev_dict = params["device"]
        if dev_name == "linux_srv1":
            continue
        print("-" * 80)
        print(f"Device name: {dev_name}")
        print("-" * 12)

        dev_dict["password"] = PASSWORD
        if dev_name == "cisco_asa":
            dev_dict["secret"] = PASSWORD
        elif dev_name == "hp_procurve":
            dev_dict["password"] = HP_PASSWORD

        # Run tests
        operations = [
            "connect",
            "send_command_simple",
            # "save_config",
            "send_config_simple",
            "send_config_large_acl",
            "cleanup",
        ]
        results = {}
        platform = dev_dict["device_type"]
        for op in operations:
            func = globals()[op]
            time_delta, result = func(dev_dict)
            if op != "cleanup":
                results[op] = time_delta
            # Some platforms have an issue where the last test affects the
            # next test?
            if "procurve" in platform:
                print("Sleeping 30 seconds...")
                time.sleep(30)
                print("Done")
        print("-" * 80)
        print()

        write_csv(dev_name, results)

    print("\n\n")


def test_performance():
    main()


if __name__ == "__main__":
    main()
