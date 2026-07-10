from __future__ import annotations

import dataclasses
import logging
import pathlib
import re
import sys
import typing

import yaml

from htp.config import Config
from htp.report import ConfigPolicy
from htp.report import ConfigReport
from htp.report import ContextEnd
from htp.report import FixType
from htp.report import HtmlGroup
from htp.report import LinePolicy
from htp.report import PolicyOut
from htp.report import PolicyStats
from htp.report import ReportOutput
from htp.report import ReportOutputs
from htp.report import ReportOutputsModel

if typing.TYPE_CHECKING:
    from htp.report import Regions

SPACER = ".."
CONFIG_DIRECTORY = "configs"

logger = logging.getLogger(__name__)


class CompiledLinePolicy:
    def __init__(
        self,
        line_policy: LinePolicy,
        includer: Includer,
        variables: dict[str, str],
        depth: int = 0,
    ):
        self.hits = 0
        self.cache = {}
        self._compiled = None
        self.line_policy = line_policy
        included = includer.include(line_policy)
        self.line_policies = []
        logger.log(
            9,
            "%sCompiling '%s'",
            " " * depth,
            self.line_policy.pattern,
        )
        for policy in included:
            policy.populate(variables=variables)
            self.line_policies.append(
                CompiledLinePolicy(
                    policy,
                    includer,
                    variables,
                    depth + 1,
                ),
            )
        count = self.line_policy.count
        if self.line_policy.group is HtmlGroup.INVALID:
            # count is ignored to keep this simpler
            self.min = 0
            self.max = 0
        elif count.isdigit():
            self.min = int(count)
            self.max = int(count)
        elif count == "+":
            self.min = 1
            self.max = sys.maxsize
        elif count == "*":
            self.min = 0
            self.max = sys.maxsize
        else:
            v1, v2 = count.split(",")
            self._min = 0 if not v1 else int(v1)
            self._max = sys.maxsize if not v2 else int(v1)

    @property
    def compiled(self) -> re.Pattern:
        if self._compiled is not None:
            return self._compiled
        _pattern = self.line_policy.pattern
        if not self.line_policy.regex:
            _pattern = r"^" + re.escape(self.line_policy.pattern) + r"$"
        _flags = re.NOFLAG
        if self.line_policy.icase:
            _flags |= re.IGNORECASE
        if self.line_policy.regex:
            _flags |= self.line_policy.flags
        self._compiled = re.compile(_pattern, flags=_flags)
        return self._compiled

    def _match(self, string) -> re.Match | None:
        if m := self.cache.get(string):
            self.hits += 1
            return m
        if not (m := self.compiled.match(string)):
            return
        self.hits = 1
        self.cache[string] = m
        return m

    def is_match(self, string) -> bool:
        return bool(self._match(string))

    def sub(self, substr, string) -> str:
        return self.compiled.sub(substr, string)

    def groups(self, string) -> tuple:
        if not (m := self._match(string)):
            return ()
        return m.groups()

    def groupdict(self, string) -> dict:
        if not (m := self._match(string)):
            return {}
        return m.groupdict()

    def met_minimum(self):
        return self.hits >= self.min

    def within_max(self):
        return self.hits <= self.max

    def under_max(self):
        return self.max and self.hits < self.max

    def valid(self):
        return self.met_minimum() and self.within_max()

    def get_stats(self) -> PolicyStats:
        return PolicyStats(
            min=self.min,
            max=self.max,
            hits=self.hits,
        )

    def fix(self, line: str | None = None) -> str:
        match line, self.line_policy.fix:
            case _, FixType.NONE:
                return ""
            case _, FixType.TEXT:
                return self.line_policy.fix_text
            case _, FixType.COPY:
                return self.line_policy.pattern
            case None, FixType.PREFIX_NO:
                raise RuntimeError(f"No string provided for no-prefix")
            case _, FixType.PREFIX_NO:
                # invert if no exists
                _PREFIX_NO = "no "
                if line.startswith(_PREFIX_NO):
                    return line.replace(_PREFIX_NO, "")
                return f"{_PREFIX_NO}{line}"
            case None, FixType.SUB:
                raise RuntimeError(f"No string provided for sub")
            case _, FixType.SUB:
                return self.sub(self.line_policy.fix_text, line)

    def debug_report(self):
        print(
            f"{self.line_policy.pattern}: {self.hits} {self.valid()=}",
        )


class Includer:
    def __init__(self, config: Config):
        INCLUDE_DIRECTORY = config.policy.include_dir
        self._include_cache = {"": []}
        for include in pathlib.Path(INCLUDE_DIRECTORY).glob(
            "*.y*ml",
        ):
            with open(include) as file:
                self._include_cache[include.stem] = yaml.safe_load(file)

    def _include(self, ruleset: str) -> list[LinePolicy]:
        return [LinePolicy(**p) for p in self._include_cache[ruleset]]

    def include(self, lp: LinePolicy | ConfigPolicy) -> list[LinePolicy]:
        """
        The object needs to have include_before, line_policies and include_after
        """
        line_policies = []
        for incl in lp.include_before:
            line_policies.extend(self._include(incl))
        line_policies.extend(lp.line_policies)
        for incl in lp.include_after:
            line_policies.extend(self._include(incl))
        return line_policies

    def include_vars(self, cp: ConfigPolicy) -> dict:
        """
        The object needs to have vars_before, static_variables and vars_after
        """
        variables = {}
        for _vars in cp.vars_before:
            variables.update(self._include_cache[_vars])
        variables.update(cp.static_variables)
        for _vars in cp.vars_after:
            variables.update(self._include_cache[_vars])
        return variables


def hash_from_line_policies(lps: list[LinePolicy]) -> str:
    import hashlib

    string = ""
    for lp in lps:
        data = lp.model_dump()
        data.pop("idx", None)  # these are randomly generated
        if data.pop("line_policies", None):  # use recursion for nested policies
            string += hash_from_line_policies(lp.line_policies)
        string += str(data)
    return hashlib.md5(string.encode()).hexdigest()


class CompiledConfigPolicy:
    def __init__(
        self,
        policy: ConfigPolicy,
        includer: Includer,
        config: Config,
    ):
        self.policy = policy
        self.includer = includer
        included = includer.include(policy)
        variables = includer.include_vars(policy)
        self.config = open(config.backups.running_dir / policy.filename).read()
        self.datahash = hash_from_line_policies(included)

        self.line_policies = []
        for line_policy in included:
            line_policy.populate(variables=variables)
            self.line_policies.append(
                CompiledLinePolicy(
                    line_policy,
                    includer,
                    self.policy.static_variables,
                ),
            )


@dataclasses.dataclass
class Context:
    pattern: str
    policies: list[CompiledLinePolicy]
    fix_tree: dict[str, dict]
    indent: int = 0
    end: ContextEnd = ContextEnd.EOF
    line: str = ""
    lineno: int = 0
    region: Regions | None = None
    depth: int = 0

    def __post_init__(self):
        logger.log(9, "%s -> %s", SPACER * self.depth, self.pattern)


def apply_policies(
    string: str,
    line_policies: list[CompiledLinePolicy],
) -> ConfigReport:
    idx = pidx = 0
    lineno = 0
    indent = 0

    ignored = {}
    valid = {}
    invalid = {}
    fixes = {}
    untested = []
    _regions = []
    fix_tree = {}
    contexts = [Context("default", line_policies, fix_tree)]
    terminate = False
    regions: dict[str, set[int]] = {}

    def _active_policies(
        lps: list[CompiledLinePolicy],
    ) -> typing.Iterable[CompiledLinePolicy]:
        for lp in lps:
            if lp.under_max:
                yield lp

    def _add_fixline(fix: str, idx: str):
        if not fix:
            return
        fixes.setdefault(contexts[-1].lineno, []).append((fix, idx))

    def _add_fix(fix: str):
        if not fix:
            return
        contexts[-1].fix_tree.setdefault(fix, {})

    def _resolve_fixes(line_policy: CompiledLinePolicy) -> dict:
        if not line_policy.line_policies:
            return {}
        result = {}
        for lp in line_policy.line_policies:
            if not lp.met_minimum():
                fix = lp.fix()
                result[fix] = _resolve_fixes(lp)
                _add_fixline(fix, lp.line_policy.idx)
        return result

    def _enter(lp: CompiledLinePolicy):
        if _regions:
            regions.setdefault(_regions[0].value, set()).add(lineno)
        if not lp.line_policies:
            return
        contexts.append(
            Context(
                pattern=lp.line_policy.pattern,
                policies=lp.line_policies,
                fix_tree={},
                indent=indent,
                end=lp.line_policy.context_end,
                line=line,
                lineno=lineno,
                region=lp.line_policy.region or contexts[-1].region,
                depth=contexts[-1].depth + 1,
            ),
        )

    def _exit():
        if not contexts:
            raise RuntimeError("Unexpected context exit")
        logger.log(9, "%s <- %s", contexts[-1].depth * SPACER, contexts[-1].pattern)
        for lp in contexts[-1].policies:
            if not lp.met_minimum():
                fix = lp.fix()
                contexts[-1].fix_tree.setdefault(fix, {}).update(_resolve_fixes(lp))
                _add_fixline(fix, lp.line_policy.idx)
        context = contexts.pop()
        if context.end is ContextEnd.EOF and idx < len(string):
            raise RuntimeError("unexpected eof")
        if context.end is ContextEnd.EOF:
            return
        if not context.fix_tree:
            return
        contexts[-1].fix_tree.setdefault(context.line, {}).update(context.fix_tree)

    while idx < len(string):
        lineno += 1
        indent = 0
        while idx < len(string) and string[idx] == " ":
            indent += 1
            idx += 1
        while idx < len(string) and string[idx] != "\n":
            idx += 1
        line = string[pidx + indent : idx]
        idx += 1
        pidx = idx

        while True:
            if (
                contexts[-1].end is ContextEnd.INDENT_END
                and contexts[-1].indent >= indent
            ):
                _exit()
                continue
            break

        if terminate and contexts[-1].end is ContextEnd.AT_TERMINATOR:
            terminate = False
            _exit()
        elif terminate:
            raise RuntimeError("Unexpected terminator without context")

        if region := contexts[-1].region:
            regions.setdefault(region.value, set()).add(lineno)

        if not line:
            regions.setdefault("ignore", set()).add(lineno)
            continue

        for lp in _active_policies(contexts[-1].policies):
            if lp.is_match(line):
                logger.log(
                    9,
                    "%s line %04d matches '%s'",
                    SPACER * contexts[-1].depth,
                    lineno,
                    lp.line_policy.pattern,
                )
                break
        else:
            logger.log(
                9,
                "%s line %04d no match",
                SPACER * contexts[-1].depth,
                lineno,
            )
            untested.append(lineno)
            continue

        if lp.line_policy.is_terminator:
            terminate = True
        _regions[:] = []
        if lp.line_policy.region:
            _regions.append(lp.line_policy.region)
        match lp.line_policy.group:
            case HtmlGroup.IGNORED:
                ignored[lineno] = lp.line_policy.idx
            case HtmlGroup.VALID:
                valid[lineno] = lp.line_policy.idx
            case HtmlGroup.INVALID:
                invalid[lineno] = lp.line_policy.idx
                fix = lp.fix(line)
                _add_fix(fix)
                _add_fixline(fix, lp.line_policy.idx)
            case HtmlGroup.NONE:
                logger.error(
                    "No Group assigned: %04d %s %s",
                    lineno,
                    line,
                    lp.line_policy.group,
                )

        _enter(lp)
    else:
        _exit()
    if contexts:
        raise RuntimeError("unexpected contexts remaining")

    fix_text = []

    def _resolve_fix_text(_fix_tree, depth=0):
        for line, subtree in _fix_tree.items():
            if line:
                fix_text.append(" " * depth + line)
                _resolve_fix_text(subtree, depth + 1)

    _resolve_fix_text(fix_tree)

    indexed_policies = {}

    def _resolve_index_contexts(_policies: list[CompiledLinePolicy], parent=""):
        for lp in _policies:
            indexed_policies[lp.line_policy.idx] = PolicyOut(
                parent=parent,
                stats=lp.get_stats(),
                policy=lp.line_policy,
            )
            _resolve_index_contexts(lp.line_policies, lp.line_policy.idx)

    _resolve_index_contexts(line_policies)

    return ConfigReport(
        valid={
            lno: p
            for lno, p in valid.items()
            if lno not in regions.get("ignore", set())
        },
        invalid=invalid,
        untested=[lno for lno in untested if lno not in regions.get("ignore", set())],
        fix_tree=fix_tree,
        fixes=fixes,
        fix_text=fix_text,
        lines=lineno,
        policies=indexed_policies,
        regions={k: list(sorted(v)) for k, v in regions.items()},
    )


def get_policy_from_file(
    filename: pathlib.Path,
    config: Config,
    includer: Includer,
) -> CompiledConfigPolicy:
    logger.info("Opening policy file: %s", filename)
    with open(filename) as file:
        contents = file.read()
    raw_policy = yaml.safe_load(contents)
    return CompiledConfigPolicy(
        policy=ConfigPolicy(**raw_policy),
        includer=includer,
        config=config,
    )


def run_analysis(config: Config, policy_files: typing.Iterable[pathlib.Path]):
    outputs: ReportOutputs = []
    includer = Includer(config)
    for filename in policy_files:
        try:
            compiled = get_policy_from_file(filename, config, includer)
            output = ReportOutput(
                filename=compiled.policy.filename,
                report=apply_policies(compiled.config, compiled.line_policies),
                datahash=compiled.datahash,
            )
            logger.info(f"Report complete for %s", filename)
            outputs.append(output)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            logger.error("Error opening file: %s (%s)", filename, exc)

    with open(config.policy.output_file, "wb") as file:
        file.write(
            ReportOutputsModel.dump_json(
                outputs,
                exclude_defaults=True,
                indent=4,
            ),
        )


def output_html_report(config: Config):
    from htp.html import Coverage
    from htp.html import HtmlReporter

    coverer = Coverage(config.policy.output_file, config)
    reporter = HtmlReporter(coverer)
    reporter.report()
