from __future__ import annotations

import enum
import pathlib
import re
import uuid
from typing import Any

import pydantic

PolicyID = str
GroupMatch = dict[int, PolicyID]
FixSet = dict[int, list[tuple[str, PolicyID]]]

_EXTRACT_VAR_PATTERN = re.compile(
    r"\{\{\s*([a-z][a-z0-9_-]*)\s*\}\}",
    flags=re.IGNORECASE,
)


def _test_valid_varname(var):
    if not (var.isupper() or var.islower()):
        raise RuntimeError("mixed case not supported")


def get_string(string, variables: dict[str, str]) -> str:
    if not (match := _EXTRACT_VAR_PATTERN.search(string)):
        return string
    varname = match.group(1)
    _test_valid_varname(varname)
    if not varname.islower():
        return string
    start, stop = match.span()
    var = variables.get(varname)
    if var is None:
        raise RuntimeError(f"{var} not defined")
    return string[:start] + var + string[stop:]


class ConfigReport(pydantic.BaseModel):
    valid: GroupMatch
    invalid: GroupMatch
    untested: list[int]
    fixes: FixSet
    fix_text: list[str]
    fix_tree: dict
    lines: int
    policies: dict[PolicyID, PolicyOut]
    regions: dict[str, list[int]]


class ReportOutput(pydantic.BaseModel):
    filename: str
    datahash: str
    report: ConfigReport

    @classmethod
    def list_from_file(cls, analysis_file: pathlib.Path) -> list[ReportOutput]:
        import json

        with open(analysis_file) as file:
            data = json.load(file)
            return [cls(**o) for o in data]


ReportOutputs = list[ReportOutput]
ReportOutputsModel = pydantic.TypeAdapter(ReportOutputs)


class PolicyStats(pydantic.BaseModel):
    min: int
    max: int
    hits: int


class PolicyOut(pydantic.BaseModel):
    parent: PolicyID
    stats: PolicyStats
    policy: LinePolicy

    @pydantic.field_validator("policy", mode="before")
    @classmethod
    def remove_nested_policies(cls, data: Any) -> Any:
        if isinstance(data, LinePolicy):
            return data.model_copy(
                update={
                    "line_policies": [],
                },
            )
        elif isinstance(data, dict):
            data.pop("line_policies", None)
            return data
        raise ValueError("invalid policy out data")


class Regions(enum.StrEnum):
    NONE = "none"
    IGNORE = "ignore"
    INTERFACE = "interface"
    PROTOCOL = "protocol"


class HtmlGroup(enum.StrEnum):
    NONE = "none"
    VALID = "valid"
    INVALID = "invalid"
    IGNORED = "ignored"


class FixType(enum.StrEnum):
    NONE = "none"
    TEXT = "text"
    SUB = "sub"
    COPY = "copy"
    PREFIX_NO = "prefix-no"


class ContextEnd(enum.StrEnum):
    EOF = "eof"
    INDENT_END = "indent-end"
    AT_TERMINATOR = "at-terminator"


class LinePolicy(pydantic.BaseModel):
    idx: str = pydantic.Field(
        default_factory=lambda: uuid.uuid4().hex,
        exclude=True,
    )
    desc: str = ""
    pattern: str
    regex: bool = False
    icase: bool = False
    flags: re.RegexFlag = re.NOFLAG
    count: str = "1"
    group: HtmlGroup = HtmlGroup.VALID
    is_terminator: bool = False
    context_end: ContextEnd = ContextEnd.INDENT_END
    region: Regions | None = None
    line_policies: list[LinePolicy] = pydantic.Field(default_factory=list)
    fix: FixType = FixType.COPY
    fix_text: str = ""
    include_before: list[str] = pydantic.Field(default_factory=list)
    include_after: list[str] = pydantic.Field(default_factory=list)

    @pydantic.model_serializer(mode="wrap")
    def serialize_model(
        self,
        handler: pydantic.SerializerFunctionWrapHandler,
    ) -> dict[str, object]:
        """
        serialize StrEnum as str
        """
        serialized = handler(self)
        for key in serialized:
            if issubclass(type(serialized[key]), enum.StrEnum):
                serialized[key] = str(serialized[key])
        return serialized

    @pydantic.field_validator("count", mode="after")
    @classmethod
    def validate_count_syntax(cls, value: str) -> str:
        if value.isdigit():
            return value
        if value == "*":
            return value
        if value == "+":
            return value
        values = value.split(",")
        if values == 2:
            v1, v2 = values
            one_number = v1 or v2
            v1valid = not v1 or v1.isdigit()
            v2valid = not v2 or v2.isdigit()
            if v1valid and v2valid and one_number:
                return value
        raise ValueError("Invalid count syntax: {count!r}")

    def populate(self, *, variables: dict):
        self.pattern = get_string(self.pattern, variables)
        self.fix_text = get_string(self.fix_text, variables)


class ConfigPolicy(pydantic.BaseModel):
    filename: str
    static_variables: dict[str, str] = pydantic.Field(default_factory=dict)
    line_policies: list[LinePolicy] = pydantic.Field(default_factory=list)
    include_before: list[str] = pydantic.Field(default_factory=list)
    include_after: list[str] = pydantic.Field(default_factory=list)
