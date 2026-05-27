from __future__ import annotations

import pathlib
import tomllib

import pydantic

DEFAULT_CONFIG_FILE = "htp.toml"


class HtmlConfig(pydantic.BaseModel):
    output_dir: pathlib.Path
    show_contexts: bool = True
    report_contexts: list = pydantic.Field(default_factory=list)
    skip_empty: bool = False
    html_skip_covered: bool = False
    skip_covered: bool = False
    html_skip_empty: bool = False
    html_title: str = "HTP Policy Report"
    extra_css: str = ""
    precision: int = 2


class PolicyConfig(pydantic.BaseModel):
    output_file: pathlib.Path
    include_dir: pathlib.Path
    policies_dir: pathlib.Path


class BackupsConfig(pydantic.BaseModel):
    running_dir: pathlib.Path


class Config(pydantic.BaseModel):
    name: str
    html: HtmlConfig
    policy: PolicyConfig
    backups: BackupsConfig


def load_config(path: pathlib.Path | str = DEFAULT_CONFIG_FILE):
    with open(path, "rb") as file:
        return Config(**tomllib.load(file))
