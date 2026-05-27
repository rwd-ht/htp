# Originally from Coverage.py https://github.com/coveragepy/coveragepy/
# See licenses/LICENSE-COVERAGE
# Copyright 2001 Gareth Rees.  All rights reserved.
# Copyright 2004-2026 Ned Batchelder
# Copyright 2026 HyeTech

from __future__ import annotations

import collections
import dataclasses
import datetime
import functools
import json
import logging
import os
import pathlib
import re
import string
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from itertools import groupby
from operator import itemgetter
from typing import Any

from htp.config import Config
from htp.cov import __version__
from htp.cov.files import flat_rootname
from htp.cov.misc import Hasher
from htp.cov.misc import ensure_dir
from htp.cov.misc import file_be_gone
from htp.cov.misc import format_local_datetime
from htp.cov.misc import human_sorted
from htp.cov.misc import plural
from htp.cov.misc import stdout_link
from htp.cov.templite import Templite

__url__ = f"https://place.holder/{__version__}"

logger = logging.getLogger(__name__)


class AnalysisNarrower:
    """
    For reducing an `Analysis` to a subset of its lines.

    Originally this was a simpler method on Analysis, but that led to quadratic
    behavior.  This class does the bulk of the work up-front to provide the
    same results in linear time.

    Create an AnalysisNarrower from an Analysis, bulk-add region lines to it
    with `add_regions`, then individually request new narrowed Analysis objects
    for each region with `narrow`.  Doing most of the work in limited calls to
    `add_regions` lets us avoid poor performance.
    """

    # In this class, regions are represented by a frozenset of their lines.

    def __init__(self, analysis: Analysis) -> None:
        self.analysis = analysis

    def add_regions(self, liness: Iterable[set[int]]) -> None:
        pass

    def narrow(self, lines: set[int]) -> Analysis:
        """Create a narrowed Analysis.

        The current analysis is copied to make a new one that only considers
        the lines in `lines`.
        """

        # Technically, the set intersections in this method are still O(N**2)
        # since this method is called N times, but they're very fast and moving
        # them to `add_regions` won't avoid the quadratic time.

        valid = self.analysis.valid & lines
        invalid = self.analysis.invalid & lines
        untested = self.analysis.untested & lines
        fixes = {k: v for k, v in self.analysis.fixes.items() if k in lines}

        return Analysis(
            filename=self.analysis.filename,
            numbers=Numbers(precision=self.analysis.numbers.precision),
            valid=valid,
            invalid=invalid,
            untested=untested,
            fixes=fixes,
            regions=self.analysis.regions,
            fix_text=self.analysis.fix_text,
        )


def display_covered(pc: float, precision: int) -> str:
    """Return a displayable total percentage, as a string.

    Note that "0" is only returned when the value is truly zero, and "100"
    is only returned when the value is truly 100.  Rounding can never
    result in either "0" or "100".

    """
    near0 = 1.0 / 10**precision
    if 0 < pc < near0:
        pc = near0
    elif (100.0 - near0) < pc < 100:
        pc = 100.0 - near0
    else:
        pc = round(pc, precision)
    return f"{pc:.{precision}f}"


class CoverageData:
    def __init__(
        self,
        coverage: Coverage,
    ):
        self.coverage = coverage

    def hash_data(self, filename):
        return self.coverage.hash_by_filename.get(filename)

    def contexts_by_lineno(self, filename):
        data = self.coverage.data_by_filename.get(filename)
        if not data:
            return {}
        contexts = data.valid | data.invalid
        return {lineno: [context] for lineno, context in contexts.items()}


@dataclasses.dataclass
class Numbers:
    """The numerical results of measuring coverage.

    This holds the basic statistics from `Analysis`, and is used to roll
    up statistics across files.

    """

    precision: int = 0
    n_files: int = 0

    o_lines: int = 0
    o_valid: int = 0
    o_invalid: int = 0
    o_untested: int = 0
    o_fixes: int = 0

    @property
    def total_not_ignored(self) -> int:
        """all configuration lines valid for consideration"""
        return self.o_valid + self.o_invalid + self.o_untested

    @property
    def total_matched(self) -> int:
        """all configuration lines matched by a policy"""
        return self.o_valid + self.o_invalid

    @property
    def ratio_matched(self) -> tuple[int, int]:
        """Return numerator/denominator for matched configuration lines"""
        return self.total_matched, self.total_not_ignored

    @property
    def ratio_valid(self) -> tuple[int, int]:
        """Return numerator/denominator for valid vs total matched"""
        result = (
            max(self.o_lines - (self.o_invalid + self.o_fixes + self.o_untested), 0),
            self.o_lines,
        )
        return result

    def _percent(self, numerator: int, denominator: int) -> float:
        """Helper for pc_* properties."""
        if denominator > 0:
            return (100.0 * numerator) / denominator
        return 0

    @property
    def pc_matched(self) -> float:
        """Returns a single percentage value for matched lines."""
        return self._percent(*self.ratio_matched)

    @property
    def pc_valid(self) -> float:
        """Returns the percentage covered for valid lines."""
        return self._percent(*self.ratio_valid)

    @property
    def pc_matched_str(self) -> str:
        """Returns the percent covered, as a string, without a percent sign.

        Note that "0" is only returned when the value is truly zero, and "100"
        is only returned when the value is truly 100.  Rounding can never
        result in either "0" or "100".

        """
        return display_covered(self.pc_matched, self.precision)

    @property
    def pc_valid_str(self) -> str:
        """Returns the statement percent covered without a percent sign."""
        return display_covered(self.pc_valid, self.precision)

    def __add__(self, other: Numbers) -> Numbers:
        return Numbers(
            precision=self.precision,
            n_files=self.n_files + other.n_files,
            o_lines=self.o_lines + other.o_lines,
            o_valid=self.o_valid + other.o_valid,
            o_untested=self.o_untested + other.o_untested,
            o_invalid=self.o_invalid + other.o_invalid,
            o_fixes=self.o_fixes + other.o_fixes,
        )

    def __radd__(self, other: int) -> Numbers:
        # Implementing 0+Numbers allows us to sum() a list of Numbers.
        assert other == 0  # we only ever call it this way.
        return self


@dataclasses.dataclass
class Analysis:
    filename: str
    numbers: Numbers
    invalid: set
    valid: set
    untested: set
    fix_text: str
    fixes: dict[int, list[tuple[str, str]]]
    regions: dict[str, list[int]]

    def branch_stats(self):
        return []


class Coverage:
    def __init__(
        self,
        policy_output_file: pathlib.Path,
        htp_config: Config,
    ):
        from htp.report import ReportOutput

        self.htp_config = htp_config

        self.outputs = ReportOutput.list_from_file(policy_output_file)
        self.data_by_filename = {}
        self.hash_by_filename = {}
        for report in self.outputs:
            self.data_by_filename[report.filename] = report.report
            self.hash_by_filename[report.filename] = report.datahash

        self.config = htp_config

    def get_files_to_report(
        self,
    ) -> Iterable[FileToReport]:
        for filename in self.data_by_filename:
            analysis = self.get_analysis(filename)
            yield FileToReport(filename, analysis, self.htp_config)

    def get_analysis(
        self,
        filename: str | pathlib.Path,
    ):
        data = self.data_by_filename.get(str(filename))
        if not data:
            raise RuntimeError
        return Analysis(
            filename=str(filename),
            numbers=Numbers(
                precision=0,
                n_files=1,
                o_lines=data.lines,
                o_valid=len(data.valid),
                o_untested=len(data.untested),
                o_invalid=len(data.invalid),
                o_fixes=len(data.fix_text),
            ),
            valid=set(data.valid),
            invalid=set(data.invalid),
            untested=set(data.untested),
            fixes=data.fixes,
            regions=data.regions,
            fix_text="\n".join(data.fix_text),
        )

    def get_data(self) -> CoverageData:
        return CoverageData(self)

    def _warn(self, message):
        print(message)

    def _message(self, message):
        print(message)


class FileReporter:
    def __init__(
        self,
        filename: str,
        analysis: Analysis,
        htp_config: Config,
    ):
        self.htp_config = htp_config
        self.filename = filename
        self.analysis = analysis
        self._source = None
        self._lines_by_no = None

    @property
    def lines_by_no(self):
        if self._lines_by_no is not None:
            return self._lines_by_no
        self._lines_by_no = {
            lineno: line
            for lineno, line in enumerate(self.source().splitlines(), start=1)
        }
        return self._lines_by_no

    def source(self):
        if self._source is None:
            with open(self.htp_config.backups.running_dir / self.filename) as file:
                self._source = file.read()
        return self._source

    def relative_filename(self):
        return str(self.filename)

    def source_token_lines(self):
        """
        token types:
            annotate
            interface
            com
            fst
            key
            nam
            num
            op
            par
            run
            str
            txt
            ws
        """

        results = []
        for line in self.source().splitlines():
            tokens = []
            words = line.split()
            wordc = len(words)
            if not words:
                tokens.append(("ws", " "))
                results.append(tokens)
                continue
            if indent := re.search(r"^\s+", line):
                tokens.append(("ws", indent.group()))
            is_int = False
            for i, word in enumerate(words, start=1):
                if is_int:
                    is_int = False
                    tokens.append(("interface", word))
                    continue
                if i == 1 and word.startswith("interface"):
                    is_int = True
                    tokens.append(("txt", word))
                else:
                    tokens.append(("txt", word))
                if i != wordc:
                    tokens.append(("ws", " "))
            results.append(tokens)
        return results

    def code_regions(self):
        regions = []
        for name, lines in self.analysis.regions.items():
            if name == "ignore":
                continue

            lines.sort()
            for _, g in groupby(enumerate(lines), lambda ix: ix[0] - ix[1]):
                group = list(map(itemgetter(1), g))
                regions.append(
                    CodeRegion(
                        kind=name,
                        name=self.lines_by_no[group[0]].split()[-1],
                        start=group[0],
                        lines=set(group),
                    ),
                )
        return regions

    def code_region_kinds(self):
        """
        unused for now, can be used later to focus on specific chunks of config
        """
        return [
            ("interface", "interfaces"),
            ("protocol", "protocols"),
        ]


@dataclass
class CodeRegion:
    kind: str
    name: str

    #: The line in the source file to link to when navigating to the region.
    #: Can be a line not mentioned in `lines`.
    start: int

    #: The lines in the region. Should be lines that could be executed in the
    #: region.  For example, a class region includes all of the lines in the
    #: methods of the class, but not the lines defining class attributes, since
    #: they are executed on import, not as part of exercising the class.  The
    #: set can include non-executable lines like blanks and comments.
    lines: set[int]

    def __lt__(self, other: CodeRegion) -> bool:
        """To support sorting to make test-writing easier."""
        if self.name == other.name:
            return min(self.lines) < min(other.lines)
        return self.name < other.name


def data_filename(fname: str) -> str:
    """Return the path to an "htmlfiles" data file of ours."""
    static_dir = os.path.join(os.path.dirname(__file__), "htmlfiles")
    static_filename = os.path.join(static_dir, fname)
    return static_filename


def read_data(fname: str) -> str:
    """Return the contents of a data file of ours."""
    with open(data_filename(fname), encoding="utf-8") as data_file:
        return data_file.read()


def write_html(fname: str, html: str) -> None:
    """Write `html` to `fname`, properly encoded."""
    html = re.sub(r"(\A\s+)|(\s+$)", "", html, flags=re.MULTILINE) + "\n"
    with open(fname, "wb") as fout:
        fout.write(html.encode("ascii", "xmlcharrefreplace"))


@dataclass
class LineData:
    """The data for each source line of HTML output."""

    tokens: list[tuple[str, str]]
    number: int
    category: str
    contexts: list[str]
    contexts_label: str
    context_list: list[str]
    short_annotations: list[str]
    long_annotations: list[str]
    html: str = ""
    context_str: str | None = None
    annotate: str | None = None
    annotate_long: str | None = None
    css_class: str = ""


@dataclass
class FileData:
    """The data for each source file of HTML output."""

    relative_filename: str
    nums: Numbers
    lines: list[LineData]
    fix_text: str

    @property
    def fix_text_rows(self) -> int:
        return 40

    @property
    def fix_text_cols(self) -> int:
        return 100


@dataclass
class IndexItem:
    """Information for each index entry, to render an index page."""

    url: str = ""
    file: str = ""
    description: str = ""
    nums: Numbers = field(default_factory=Numbers)


@dataclass
class IndexPage:
    """Data for each index page."""

    noun: str
    plural: str
    filename: str
    summaries: list[IndexItem]
    totals: Numbers
    skipped_covered_count: int
    skipped_empty_count: int


class HtmlDataGeneration:
    """Generate structured data to be turned into HTML reports."""

    EMPTY = "(empty)"

    def __init__(self, cov: Coverage) -> None:
        self.coverage = cov
        self.config = self.coverage.config
        self.data = self.coverage.get_data()
        # if self.config.show_contexts:
        #     if self.data.measured_contexts() == {""}:
        #         self.coverage._warn("No contexts were measured")
        # self.data.set_query_contexts(self.config.report_contexts)

    def data_for_file(self, fr: FileReporter, analysis: Analysis) -> FileData:
        """Produce the data needed for one file's report."""

        contexts_by_lineno = self.data.contexts_by_lineno(analysis.filename)

        lines = []

        def _add_fix_lines(
            lineno: int,
        ):
            linepolicies = analysis.fixes.get(lineno, [])
            count = len(linepolicies)
            start = lineno * 10000 + 1
            for i, (line, policy) in zip(
                range(start, start + count),
                reversed(linepolicies),
            ):
                lines.append(
                    LineData(
                        tokens=[
                            ("fix", f">>>>"),
                            ("ws", " "),
                            ("txt", line),
                        ],
                        number=0 - i,
                        category="ofix",
                        contexts=[policy],
                        contexts_label="1 ctx",
                        context_list=[policy],
                        short_annotations=[],
                        long_annotations=[],
                    ),
                )

        _add_fix_lines(0)
        for lineno, tokens in enumerate(fr.source_token_lines(), start=1):
            category = "ount"
            category2 = ""
            short_annotations = []
            long_annotations = []

            if lineno in analysis.regions.get("ignore", []):
                category = ""
            elif lineno in analysis.invalid:
                category = "oinv"
            elif lineno in analysis.valid:
                category = "oval"

            contexts = []
            contexts_label = ""
            context_list = []
            if category and self.config.html.show_contexts:
                contexts = human_sorted(
                    c or self.EMPTY for c in contexts_by_lineno.get(lineno, ())
                )
                if contexts == [self.EMPTY]:
                    contexts_label = self.EMPTY
                else:
                    contexts_label = f"{len(contexts)} ctx"
                    context_list = contexts
            lines.append(
                LineData(
                    tokens=tokens,
                    number=lineno,
                    category=category or category2,
                    contexts=contexts,
                    contexts_label=contexts_label,
                    context_list=context_list,
                    short_annotations=short_annotations,
                    long_annotations=long_annotations,
                ),
            )
            _add_fix_lines(lineno)
        file_data = FileData(
            relative_filename=fr.relative_filename(),
            nums=analysis.numbers,
            lines=lines,
            fix_text=fr.analysis.fix_text,
        )

        return file_data


class FileToReport:
    """A file we're considering reporting."""

    def __init__(
        self,
        filename,
        analysis: Analysis,
        htp_config: Config,
    ) -> None:
        self.fr = FileReporter(filename, analysis, htp_config)
        self.filename = filename
        self.analysis = analysis
        self.rootname = flat_rootname(self.fr.relative_filename())
        self.html_filename = self.rootname + ".html"
        self.prev_html = self.next_html = ""


HTML_SAFE = string.ascii_letters + string.digits + "!#$%'()*+,-./:;=?@[]^_`{|}~"


@functools.cache
def encode_int(n: int) -> str:
    """Create a short HTML-safe string from an integer, using HTML_SAFE."""
    if n == 0:
        return HTML_SAFE[0]

    r = []
    while n:
        n, t = divmod(n, len(HTML_SAFE))
        r.append(HTML_SAFE[t])
    return "".join(r)


def copy_with_cache_bust(src: str, dest_dir: str) -> str:
    """Copy `src` to `dest_dir`, adding a hash to the name.

    Returns the updated destination file name with hash.
    """
    with open(src, "rb") as f:
        text = f.read()
    h = Hasher()
    h.update(text)
    cache_bust = h.hexdigest()[:8]
    src_base = os.path.basename(src)
    dest = src_base.replace(".", f"_cb_{cache_bust}.")
    with open(os.path.join(dest_dir, dest), "wb") as f:
        f.write(text)
    return dest


class HtmlReporter:
    """HTML reporting."""

    # These files will be copied from the htmlfiles directory to the output
    # directory.
    STATIC_FILES = [
        "style.css",
        "coverage_html.js",
        "keybd_closed.png",
        "favicon_32.png",
    ]

    def __init__(self, cov: Coverage) -> None:
        self.coverage = cov
        self.config = self.coverage.config
        self.directory = self.config.html.output_dir

        self.skip_covered = self.config.html.html_skip_covered
        if self.skip_covered is None:
            self.skip_covered = self.config.html.skip_covered
        self.skip_empty = self.config.html.html_skip_empty
        if self.skip_empty is None:
            self.skip_empty = self.config.html.skip_empty

        title = self.config.html.html_title

        self.extra_css = bool(self.config.html.extra_css)

        self.data = self.coverage.get_data()

        self.index_pages: dict[str, IndexPage] = {
            "file": self.new_index_page("file", "files"),
        }
        self.incr = IncrementalChecker(self.directory)
        self.datagen = HtmlDataGeneration(self.coverage)
        self.directory_was_empty = False
        self.first_fr = None
        self.final_fr = None

        self.template_globals = {
            # Functions available in the templates.
            "escape": escape,
            "is_negative": is_negative,
            "pair": pair,
            "pretty_file": pretty_file,
            # Constants for this report.
            "__url__": __url__,
            "__version__": __version__,
            "title": title,
            "time_stamp": format_local_datetime(datetime.datetime.now()),
            "extra_css": self.extra_css,
            "has_arcs": False,
            "statics": {},
            # Constants for all reports.
            # These css classes determine which lines are highlighted by default.
            "category": {
                "oval": "oval",
                "oinv": "oinv show_oinv",
                "ount": "ount show_ount",
                "ofix": "ofix show_ofix",
                "oval2": "oval oval2",
                "oinv2": "oinv oinv2 show_oinv",
                "ount2": "ount ount2 show_ount",
                "ofix2": "ofix ofix2 show_ofix",
            },
        }
        self.index_tmpl = Templite(read_data("index.html"), self.template_globals)
        self.pyfile_html_source = read_data("pyfile.html")
        self.source_tmpl = Templite(self.pyfile_html_source, self.template_globals)

    def new_index_page(self, noun: str, plural_noun: str) -> IndexPage:
        """Create an IndexPage for a kind of region."""
        return IndexPage(
            noun=noun,
            plural=plural_noun,
            filename="index.html" if noun == "file" else f"{noun}_index.html",
            summaries=[],
            totals=Numbers(precision=self.config.html.precision),
            skipped_covered_count=0,
            skipped_empty_count=0,
        )

    def report(self):
        """Generate an HTML report for `morfs`.

        `morfs` is a list of modules or file names.

        """
        # Read the status data and check that this run used the same
        # global data as the last run.
        self.incr.read()
        self.incr.check_global_data(
            self.config.html.model_dump_json(),
            self.pyfile_html_source,
        )

        # Process all the files. For each page we need to supply a link
        # to the next and previous page.
        files_to_report = []

        have_data = False

        for ftr in self.coverage.get_files_to_report():
            for index_page in self.index_pages.values():
                index_page.totals += ftr.fr.analysis.numbers
            self.index_pages
            have_data = True
            if self.should_report(ftr.analysis, self.index_pages["file"]):
                files_to_report.append(ftr)
            else:
                file_be_gone(os.path.join(self.directory, ftr.html_filename))

        if not have_data:
            raise RuntimeError("No data to report.")

        self.make_directory()
        self.make_local_static_report_files()

        if files_to_report:
            for ftr1, ftr2 in zip(files_to_report[:-1], files_to_report[1:]):
                ftr1.next_html = ftr2.html_filename
                ftr2.prev_html = ftr1.html_filename
            files_to_report[0].prev_html = "index.html"
            files_to_report[-1].next_html = "index.html"

        for ftr in files_to_report:
            self.write_html_page(ftr)
            continue  # disable regions for now
            for noun, plural_noun in ftr.fr.code_region_kinds():
                if noun not in self.index_pages:
                    self.index_pages[noun] = self.new_index_page(noun, plural_noun)

        # Write the index page.
        if files_to_report:
            first_html = files_to_report[0].html_filename
            final_html = files_to_report[-1].html_filename
        else:
            first_html = final_html = "index.html"
        self.write_file_index_page(first_html, final_html)

        # Write function and class index pages.
        self.write_region_index_pages(files_to_report)

    def make_directory(self) -> None:
        """Make sure our htmlcov directory exists."""
        ensure_dir(self.directory)
        if not os.listdir(self.directory):
            self.directory_was_empty = True

    def copy_static_file(self, src: str, slug: str = "") -> None:
        """Copy a static file into the output directory with cache busting."""
        dest = copy_with_cache_bust(src, self.directory)
        if not slug:
            slug = os.path.basename(src).replace(".", "_")
        self.template_globals["statics"][slug] = dest  # type: ignore

    def make_local_static_report_files(self) -> None:
        """Make local instances of static files for HTML report."""

        # The files we provide must always be copied.
        for static in self.STATIC_FILES:
            self.copy_static_file(data_filename(static))

        # The user may have extra CSS they want copied.
        if self.extra_css:
            assert self.config.html.extra_css is not None
            self.copy_static_file(self.config.html.extra_css, slug="extra_css")

        # Only write the .gitignore file if the directory was originally empty.
        # .gitignore can't be copied from the source tree because if it was in
        # the source tree, it would stop the static files from being checked in.
        if self.directory_was_empty:
            with open(
                os.path.join(self.directory, ".gitignore"),
                "w",
                encoding="utf-8",
            ) as fgi:
                fgi.write("# Created by coverage.py\n*\n")

    def should_report(self, analysis: Analysis, index_page: IndexPage) -> bool:
        """Determine if we'll report this file or region."""

        return True

    def write_html_page(self, ftr: FileToReport) -> None:
        """Generate an HTML page for one source file.

        If the page on disk is already correct based on our incremental status
        checking, then the page doesn't have to be generated, and this function
        only does page summary bookkeeping.

        """
        # Find out if the page on disk is already correct.
        if self.incr.can_skip_file(self.data, ftr.fr, ftr.rootname):
            self.index_pages["file"].summaries.append(
                self.incr.index_info(ftr.rootname),
            )
            return

        # Write the HTML page for this source file.
        file_data = self.datagen.data_for_file(ftr.fr, ftr.analysis)

        contexts = collections.Counter(
            c for cline in file_data.lines for c in cline.contexts
        )
        context_codes = {
            y: i for (i, y) in enumerate(x[0] for x in contexts.most_common())
        }
        if context_codes:
            contexts_json = json.dumps(
                {encode_int(v): k for (k, v) in context_codes.items()},
                indent=2,
            )
        else:
            contexts_json = None

        for ldata in file_data.lines:
            # Build the HTML for the line.
            html_parts = []
            for tok_type, tok_text in ldata.tokens:
                if tok_type == "ws":
                    html_parts.append(escape(tok_text))
                else:
                    tok_html = escape(tok_text) or "&nbsp;"
                    html_parts.append(f'<span class="{tok_type}">{tok_html}</span>')
            ldata.html = "".join(html_parts)
            if ldata.context_list:
                encoded_contexts = [
                    encode_int(context_codes[c_context])
                    for c_context in ldata.context_list
                ]
                code_width = max(len(ec) for ec in encoded_contexts)
                ldata.context_str = str(code_width) + "".join(
                    ec.ljust(code_width) for ec in encoded_contexts
                )
            else:
                ldata.context_str = ""

            if ldata.short_annotations:
                # 202F is NARROW NO-BREAK SPACE.
                # 219B is RIGHTWARDS ARROW WITH STROKE.
                ldata.annotate = ",&nbsp;&nbsp; ".join(
                    f"{ldata.number}&#x202F;&#x219B;&#x202F;{d}"
                    for d in ldata.short_annotations
                )
            else:
                ldata.annotate = None

            if ldata.long_annotations:
                longs = ldata.long_annotations
                # A line can only have two branch destinations. If there were
                # two missing, we would have written one as "always raised."
                assert (
                    len(longs) == 1
                ), f"Had long annotations in {ftr.fr.relative_filename()}: {longs}"
                ldata.annotate_long = longs[0]
            else:
                ldata.annotate_long = None

            css_classes = []
            if ldata.category:
                css_classes.append(
                    self.template_globals["category"][ldata.category],  # type: ignore[index]
                )
            ldata.css_class = " ".join(css_classes) or "pln"

        html_path = os.path.join(self.directory, ftr.html_filename)
        html = self.source_tmpl.render(
            {
                **file_data.__dict__,
                "fix_text_rows": file_data.fix_text_rows,
                "fix_text_cols": file_data.fix_text_cols,
                "contexts_json": contexts_json,
                "prev_html": ftr.prev_html,
                "next_html": ftr.next_html,
            },
        )
        write_html(html_path, html)

        # Save this file's information for the index page.
        index_info = IndexItem(
            url=ftr.html_filename,
            file=escape(ftr.fr.relative_filename()),
            nums=ftr.analysis.numbers,
        )
        self.index_pages["file"].summaries.append(index_info)
        self.incr.set_index_info(ftr.rootname, index_info)

    def write_file_index_page(self, first_html: str, final_html: str) -> None:
        """Write the file index page for this report."""
        index_file = self.write_index_page(
            self.index_pages["file"],
            first_html=first_html,
            final_html=final_html,
        )

        print_href = stdout_link(index_file, f"file://{os.path.abspath(index_file)}")
        self.coverage._message(f"Wrote HTML report to {print_href}")

        # Write the latest hashes for next time.
        self.incr.write()

    def write_region_index_pages(self, files_to_report: Iterable[FileToReport]) -> None:
        """Write the other index pages for this report."""
        return  # disable regions for now
        for ftr in files_to_report:
            region_nouns = [pair[0] for pair in ftr.fr.code_region_kinds()]
            num_lines = len(ftr.fr.source().splitlines())
            regions = ftr.fr.code_regions()

            for noun in region_nouns:
                page_data = self.index_pages[noun]

                outside_lines = set(range(1, num_lines + 1))
                for region in regions:
                    if region.kind != noun:
                        continue
                    outside_lines -= region.lines

                narrower = AnalysisNarrower(ftr.analysis)
                narrower.add_regions(r.lines for r in regions if r.kind == noun)
                narrower.add_regions([outside_lines])

                for region in regions:
                    if region.kind != noun:
                        continue
                    analysis = narrower.narrow(region.lines)
                    if not self.should_report(analysis, page_data):
                        continue
                    sorting_name = region.name.rpartition(".")[-1].lstrip("_")
                    page_data.summaries.append(
                        IndexItem(
                            url=f"{ftr.html_filename}#t{region.start}",
                            file=escape(ftr.fr.relative_filename()),
                            description=(
                                f"<data value='{escape(sorting_name)}'>"
                                + escape(region.name)
                                + "</data>"
                            ),
                            nums=analysis.numbers,
                        ),
                    )

                analysis = narrower.narrow(outside_lines)
                if self.should_report(analysis, page_data):
                    page_data.summaries.append(
                        IndexItem(
                            url=ftr.html_filename,
                            file=escape(ftr.fr.relative_filename()),
                            description=(
                                "<data value=''>"
                                + f"<span class='no-noun'>(no {escape(noun)})</span>"
                                + "</data>"
                            ),
                            nums=analysis.numbers,
                        ),
                    )

        for noun, index_page in self.index_pages.items():
            if noun != "file":
                self.write_index_page(index_page)

    def write_index_page(self, index_page: IndexPage, **kwargs: str) -> str:
        """Write an index page specified by `index_page`.

        Returns the filename created.
        """
        skipped_covered_msg = skipped_empty_msg = ""
        if n := index_page.skipped_covered_count:
            things = plural(n, index_page.noun, index_page.plural)
            skipped_covered_msg = f"{things} skipped due to complete coverage."
        if n := index_page.skipped_empty_count:
            things = plural(n, "empty " + index_page.noun, "empty " + index_page.plural)
            skipped_empty_msg = f"{things} skipped."

        index_buttons = [
            {
                "label": ip.plural.title(),
                "url": ip.filename if ip.noun != index_page.noun else "",
                "current": ip.noun == index_page.noun,
            }
            for ip in self.index_pages.values()
        ]
        render_data = {
            "regions": index_page.summaries,
            "totals": index_page.totals,
            "noun": index_page.noun,
            "region_noun": index_page.noun if index_page.noun != "file" else "",
            "skip_covered": self.skip_covered,
            "skipped_covered_msg": skipped_covered_msg,
            "skipped_empty_msg": skipped_empty_msg,
            "first_html": "",
            "final_html": "",
            "index_buttons": index_buttons,
        }
        render_data.update(kwargs)
        html = self.index_tmpl.render(render_data)

        index_file = os.path.join(self.directory, index_page.filename)
        write_html(index_file, html)
        return index_file


@dataclass
class FileInfo:
    """Summary of the information from last rendering, to avoid duplicate work."""

    hash: str = ""
    index: IndexItem = field(default_factory=IndexItem)


class IncrementalChecker:
    """Logic and data to support incremental reporting.

    When generating an HTML report, often only a few of the source files have
    changed since the last time we made the HTML report.  This means previously
    created HTML pages can be reused without generating them again, speeding
    the command.

    This class manages a JSON data file that captures enough information to
    know whether an HTML page for a .py file needs to be regenerated or not.
    The data file also needs to store all the information needed to create the
    entry for the file on the index page so that if the HTML page is reused,
    the index page can still be created to refer to it.

    The data looks like::

        {
            "note": "This file is an internal implementation detail ...",
            // A fixed number indicating the data format.  STATUS_FORMAT
            "format": 5,
            // The version of coverage.py
            "version": "7.4.4",
            // A hash of a number of global things, including the configuration
            // settings and the pyfile.html template itself.
            "globals": "540ee119c15d52a68a53fe6f0897346d",
            "files": {
                // An entry for each source file keyed by the flat_rootname().
                "z_7b071bdc2a35fa80___init___py": {
                    // Hash of the source, the text of the .py file.
                    "hash": "e45581a5b48f879f301c0f30bf77a50c",
                    // Information for the index.html file.
                    "index": {
                        "url": "z_7b071bdc2a35fa80___init___py.html",
                        "file": "cogapp/__init__.py",
                        "description": "",
                        // The Numbers for this file.
                        "nums": { "precision": 2, "n_files": 1, "n_statements": 43, ... }
                    }
                },
                ...
            }
        }

    """

    STATUS_FILE = "status.json"
    STATUS_FORMAT = 5
    NOTE = (
        "This file is an internal implementation detail to speed up HTML report"
        + " generation. Its format can change at any time. You might be looking"
        + " for the JSON report: https://coverage.rtfd.io/cmd.html#cmd-json"
    )

    def __init__(self, directory: str) -> None:
        self.directory = directory
        self._reset()

    def _reset(self) -> None:
        """Initialize to empty. Causes all files to be reported."""
        self.globals = ""
        self.files: dict[str, FileInfo] = {}

    def read(self) -> None:
        """Read the information we stored last time."""
        status = {}
        try:
            status_file = os.path.join(self.directory, self.STATUS_FILE)
            with open(status_file, encoding="utf-8") as fstatus:
                status = json.load(fstatus)
        except (OSError, ValueError):
            # Status file is missing or malformed.
            usable = False
        else:
            if status["format"] != self.STATUS_FORMAT:
                usable = False
            elif status["version"] != __version__:
                usable = False
            else:
                usable = True

        if usable:
            self.files = {}
            for filename, filedict in status["files"].items():
                indexdict = filedict["index"]
                index_item = IndexItem(**indexdict)
                index_item.nums = Numbers(**indexdict["nums"])
                fileinfo = FileInfo(
                    hash=filedict["hash"],
                    index=index_item,
                )
                self.files[filename] = fileinfo
            self.globals = status["globals"]
        else:
            self._reset()

    def write(self) -> None:
        """Write the current status."""
        status_file = os.path.join(self.directory, self.STATUS_FILE)
        status_data = {
            "note": self.NOTE,
            "format": self.STATUS_FORMAT,
            "version": __version__,
            "globals": self.globals,
            "files": {
                fname: dataclasses.asdict(finfo) for fname, finfo in self.files.items()
            },
        }
        with open(status_file, "w", encoding="utf-8") as fout:
            json.dump(status_data, fout, separators=(",", ":"))

    def check_global_data(self, *data: Any) -> None:
        """Check the global data that can affect incremental reporting.

        Pass in whatever global information could affect the content of the
        HTML pages.  If the global data has changed since last time, this will
        clear the data so that all files are regenerated.

        """
        h = Hasher()
        for d in data:
            h.update(d)
        these_globals = h.hexdigest()
        if self.globals != these_globals:
            self._reset()
            self.globals = these_globals

    def can_skip_file(
        self,
        data: CoverageData,
        fr: FileReporter,
        rootname: str,
    ) -> bool:
        """Can we skip reporting this file?

        `data` is a CoverageData object, `fr` is a `FileReporter`, and
        `rootname` is the name being used for the file.

        Returns True if the HTML page is fine as-is, False if we need to recreate
        the HTML page.

        """
        h = Hasher()
        h.update(fr.source().encode("utf-8"))
        hashdata = data.hash_data(fr.filename)
        h.update(hashdata)
        this_hash = h.hexdigest()

        file_info = self.files.setdefault(rootname, FileInfo())

        if this_hash == file_info.hash:
            logger.debug("Skipping %s due to matching hash", fr.filename)
            # Nothing has changed to require the file to be reported again.
            return True
        else:
            logger.info("Updating %s", fr.filename)
            # File has changed, record the latest hash and force regeneration.
            file_info.hash = this_hash
            return False

    def index_info(self, fname: str) -> IndexItem:
        """Get the information for index.html for `fname`."""
        return self.files.get(fname, FileInfo()).index

    def set_index_info(self, fname: str, info: IndexItem) -> None:
        """Set the information for index.html for `fname`."""
        self.files.setdefault(fname, FileInfo()).index = info


# Helpers for templates and generating HTML


def is_negative(i: int) -> bool:
    return i < 0


def escape(t: str) -> str:
    """HTML-escape the text in `t`.

    This is only suitable for HTML text, not attributes.

    """
    # Convert HTML special chars into HTML entities.
    if t is None:
        return str(t)
    return t.replace("&", "&amp;").replace("<", "&lt;")


def pair(ratio: tuple[int, int]) -> str:
    """Format a pair of numbers so JavaScript can read them in an attribute."""
    return "{} {}".format(*ratio)


def pretty_file(filename: str) -> str:
    """Return a prettier version of `filename` for display."""
    return re.sub(r"[/\\]", "\N{THIN SPACE}\\g<0>\N{THIN SPACE}", filename)
