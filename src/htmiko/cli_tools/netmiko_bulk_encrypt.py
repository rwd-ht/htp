#!/usr/bin/env python

# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

from htmiko.encryption_handling import encrypt_value
from htmiko.encryption_handling import get_encryption_key

# FIX: would be better to have it read the __meta__ field for the encryption type
# if no encryption type is specified.


yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


def encrypt_htmiko_yml(
    input_file: str,
    output_file: str | None,
    encryption_type: str,
) -> None:
    # Read the input YAML file
    input_path = Path(input_file).expanduser()
    with input_path.open("r") as f:
        config = yaml.load(f)

    # Get the encryption key
    key = get_encryption_key()

    # Encrypt password and secret for each device
    for device, params in config.items():
        if isinstance(params, dict):
            if "password" in params:
                encrypted_value = encrypt_value(
                    params["password"],
                    key,
                    encryption_type,
                )
                params["password"] = encrypted_value
            if "secret" in params:
                encrypted_value = encrypt_value(params["secret"], key, encryption_type)
                params["secret"] = encrypted_value

    # Write the updated config to the output file or stdout
    if output_file:
        output_path = Path(output_file)
        with output_path.open("w") as f:
            yaml.dump(config, f)
    else:
        yaml.dump(config, sys.stdout)


def main_ep():
    sys.exit(main())


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt passwords in .htmiko.yml file",
    )
    parser.add_argument(
        "--input_file",
        default="~/.htmiko.yml",
        help="Input .htmiko.yml file (default: ~/.htmiko.yml)",
    )
    parser.add_argument(
        "--output_file",
        help="Output .htmiko.yml file with encrypted passwords (default: stdout)",
    )
    parser.add_argument(
        "--encryption-type",
        choices=["fernet", "aes128"],
        default="fernet",
        help="Encryption type to use (default: fernet)",
    )

    args = parser.parse_args()

    encrypt_htmiko_yml(args.input_file, args.output_file, args.encryption_type)

    if args.output_file:
        print(
            f"Encrypted .htmiko.yml file has been written to {Path(args.output_file).resolve()}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
