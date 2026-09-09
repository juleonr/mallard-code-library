"""Structural lint for the languages CI cannot execute.

SAS and Stata have no runner here, so these files are never proved to work. This checks the few
structural rules that can be checked from the text alone, and it is careful to claim nothing more.

WHY THIS IS A SCRIPT AND NOT INLINE CI BASH. The first version was six lines inside the workflow,
and it was wrong in two ways on its first execution:

  1. It flagged a Stata file for containing a semicolon. The semicolon was inside a PROSE COMMENT
     ("no 'or' option is used here; add it when reading the output by eye"). Stata does not end
     commands with semicolons, so the rule is right, but reading it out of a comment is exactly the
     unanchored-pattern failure this project pays for over and over.

  2. It required `event=` on any `model` statement in any SAS file. `event=` is a PROC LOGISTIC
     concept: it fixes which response level is modelled, because LOGISTIC defaults to the LOWER
     one and silently inverts every odds ratio. PROC GENMOD with dist=poisson has no such notion,
     so the rule fired on a correct file.

Inline CI bash is unreviewed code: nothing runs it but the runner, and nothing tests it at all. As
a module it gets controls, below in lint.test.py, including a file that must NOT be flagged.

WHAT THIS LINT DID NOT DO UNTIL NOW, AND SHOULD HAVE FROM THE FIRST ENTRY. Every expected.json has
always carried a `must_appear` block naming the strings each language file has to contain -- the
tie method, the offset, the response level. NOTHING READ IT. Five entries declared it and it was
inert data, so the one mechanism that could have caught `ties=efron` being dropped from a SAS file
was a rule written down and never enforced. For R and Python the gap is partly covered, because a
dropped option changes the numbers and the agreement check fails; for SAS and Stata, which nothing
executes, `must_appear` was the ONLY guard there was and it was not running.

It is enforced against CODE, never comments. A pinned default named in a comment and absent from
the statement below it is exactly the failure the block exists to catch, and a substring search
over the raw file would call that a pass.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def strip_stata_comments(text: str) -> str:
    """Remove Stata comments so a rule about CODE never reads prose.

    Stata comments: a line whose first non-space character is `*`, anything after `//`, and
    /* ... */ blocks. Only the remainder is code.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("*"):
            continue
        out.append(line.split("//", 1)[0])
    return "\n".join(out)


def strip_sas_comments(text: str) -> str:
    """Remove block and statement comments without consuming quoted SAS values.

    A statement comment starts at a statement boundary, not at multiplication's `*`.
    Quoted semicolons do not finish a statement; SAS escapes quotes by doubling them.
    """
    out, i, boundary, quote = [], 0, True, None
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    out.append(text[i + 1])
                    i += 1
                else:
                    quote = None
            i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated SAS block comment")
            out.append(" ")
            i = end + 2
            continue
        if (boundary and ch == "*") or text.startswith("%*", i):
            end = text.find(";", i)
            if end < 0:
                raise ValueError("unterminated SAS statement comment")
            out.append(" ")
            i = end + 1
            continue
        out.append(ch)
        if ch in ("'", '"'):
            quote = ch
        if ch == ";":
            boundary = True
        elif not ch.isspace():
            boundary = False
        i += 1
    return "".join(out)


def lint_stata(path: Path) -> list:
    code = strip_stata_comments(path.read_text())
    problems = []
    if ";" in code:
        offenders = [l.strip() for l in code.splitlines() if ";" in l]
        problems.append(
            f"{path}: Stata does not end commands with semicolons -- {offenders[:2]}")
    if not code.strip():
        problems.append(f"{path}: nothing but comments")
    return problems


def lint_sas(path: Path) -> list:
    raw = path.read_text()
    code = strip_sas_comments(raw)
    problems = []
    if not re.search(r"\brun\s*;", code, re.I) and not re.search(r"\bquit\s*;", code, re.I):
        problems.append(f"{path}: no run; or quit; statement, so no step is ever submitted")

    # THE RESPONSE-LEVEL DEFAULT, scoped to the procs that actually have it and applied PER STEP.
    #
    # PROC LOGISTIC models the LOWER ordered response value, so a 0/1 outcome without event='1'
    # inverts every odds ratio and nothing in the listing says so. SO DOES PROC GENMOD WITH A
    # BINOMIAL DISTRIBUTION, which this rule missed: its scope was written from a GENMOD dist=
    # poisson file, where there is genuinely no such notion, and generalised to all of GENMOD.
    # A check asserting its own idea of its scope is this project's most repeated defect and this
    # was an instance of it -- found when the first GENMOD-binomial file arrived, which happened
    # to set event='1' anyway, so nothing would have been caught if it had not.
    #
    # Per step, because the old version tested EVERY model statement in the file as soon as one
    # PROC LOGISTIC appeared anywhere in it. A file pairing a correct LOGISTIC step with a Poisson
    # GENMOD step was flagged for the second step's statement.
    steps = [(m.group(1).lower(), code[m.start():])
             for m in re.finditer(r"\bproc\s+(\w+)\b", code, re.I)]
    for k, (name, tail) in enumerate(steps):
        body = tail if k + 1 >= len(steps) else tail[:len(tail) - len(steps[k + 1][1])]
        if name == "logistic":
            why = "PROC LOGISTIC"
        elif name == "genmod" and re.search(r"\bdist\s*=\s*bin", body, re.I):
            why = "PROC GENMOD with a binomial distribution"
        else:
            continue
        for m in re.finditer(r"\bmodel\b[^;]*;", body, re.I | re.S):
            if not re.search(r"\bmodel\s+\w+\s*\([^)]*\bevent\s*=", m.group(0), re.I):
                problems.append(
                    f"{path}: {why} model statement without event= -- "
                    f"the lower response level is modelled by default and the odds ratios invert")
    return problems


def strip_hash_comments(text: str, triple: bool = False) -> str:
    """Remove `#` comments from R or Python while leaving string literals alone.

    A plain `re.sub(r"#.*", "", ...)` would delete half of `sep = "#"` and, worse, would treat a
    `#` inside a quoted string as the start of a comment and strip the rest of the line -- the
    unanchored-pattern failure this repository keeps paying for. So this walks characters and
    tracks quote state instead.

    `triple` is for Python, which R does not have, and it does TWO things: it tracks triple-quoted
    regions so a `#` inside one does not start a comment, and it DROPS their contents. Dropping
    them is the point. A Python docstring is prose in the role a `#` comment plays in R, and the
    first version of this function kept it -- so `must_appear` could declare an option that lived
    only in a module docstring and pass, which is exactly the "described but not set" case the
    check names as the more dangerous of the two. Caught by writing a Python file whose pinned
    option appeared in its docstring and nowhere else.

    A pinned string inside an ordinary single- or double-quoted literal is still CODE and is kept:
    `cov_type='naive'` is an argument, not a description of one.
    """
    out = []
    i, n = 0, len(text)
    quote = None            # the closing delimiter we are waiting for, or None
    drop = False            # inside a triple-quoted region, whose contents are prose
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\" and i + 1 < n:      # an escaped character cannot close the string
                if not drop:
                    out.append(text[i:i + 2])
                i += 2
                continue
            if text.startswith(quote, i):
                if not drop:
                    out.append(quote)
                i += len(quote)
                quote = None
                drop = False
                continue
            if not drop:
                out.append(ch)
            i += 1
            continue
        if triple and (text[i:i + 3] == '"""' or text[i:i + 3] == "'''"):
            quote = text[i:i + 3]
            drop = True
            i += 3
            continue
        if ch == '"' or ch == "'":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# filename -> (how to reduce it to code, whether the language cares about case).
# SAS is case-insensitive as a language, so a declaration of `proc phreg` must match `PROC PHREG`.
# R, Python and Stata are all case-sensitive and are matched as written.
LANGUAGES = {
    "r": ("r.R", lambda s: strip_hash_comments(s), True),
    "python": ("python.py", lambda s: strip_hash_comments(s, triple=True), True),
    "sas": ("sas.sas", strip_sas_comments, False),
    "stata": ("stata.do", strip_stata_comments, True),
}


def lint_must_appear(entry: Path) -> list:
    """Every string an entry declares in `must_appear` must be present in that file's CODE.

    Two directions, because a rule that only checks what it was handed is a rule asserting its own
    scope -- this repository's most repeated defect, already committed once in the harness's
    hardcoded field names and once in CI's hardcoded R package list:

      * every declared string must appear in the file, and
      * every language file that EXISTS must be declared, or a new sas.sas could ship with nothing
        pinned and pass in silence.
    """
    expected_path = entry / "expected.json"
    if not expected_path.exists():
        return [f"{entry}: no expected.json"]
    try:
        declared = json.loads(expected_path.read_text()).get("must_appear", {})
    except json.JSONDecodeError as exc:
        return [f"{expected_path}: not valid JSON -- {exc}"]
    if not isinstance(declared, dict):
        return [f"{expected_path}: must_appear is not an object"]

    problems = []
    for lang, (filename, strip, cased) in LANGUAGES.items():
        path = entry / filename
        wanted = declared.get(lang)
        if not path.exists():
            if wanted:
                problems.append(
                    f"{expected_path}: must_appear names {lang} but {filename} does not exist")
            continue
        if not wanted:
            problems.append(
                f"{expected_path}: {filename} exists but must_appear declares nothing for {lang}. "
                f"An implementation with no pinned string is one nothing can check -- and for SAS "
                f"and Stata, which are never executed, nothing else checks them at all.")
            continue
        raw = path.read_text()
        code = strip(raw)
        haystack, hay_raw = (code, raw) if cased else (code.lower(), raw.lower())
        for needle in wanted:
            probe = needle if cased else needle.lower()
            if probe in haystack:
                continue
            # NAMING WHICH OF THE TWO IT IS, because they are different mistakes: a string that is
            # present only in a comment is a default someone described and did not set, which is
            # the more dangerous of the two and the one a raw substring search would pass.
            where = "present only in a comment" if probe in hay_raw else "absent"
            problems.append(
                f"{path}: must_appear declares {needle!r} and it is {where} in the code")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="lib")
    args = ap.parse_args(argv)

    root = Path(args.root)
    sas = sorted(root.glob("*/*.sas"))
    stata = sorted(root.glob("*/*.do"))
    entries = sorted(q.parent for q in root.glob("*/expected.json"))

    problems = []
    for p in sas:
        problems += lint_sas(p)
    for p in stata:
        problems += lint_stata(p)
    for e in entries:
        problems += lint_must_appear(e)

    print(f"SAS files: {len(sas)}   Stata files: {len(stata)}   "
          f"entries checked against must_appear: {len(entries)}")
    for p in problems:
        print(f"  FAIL {p}")
    if not problems:
        print("  structural lint passed: the text is well formed and every pinned string each")
        print("  entry declared is present in the code rather than only in the prose beside it.")
        print("  SAS AND STATA ARE STILL NOT EXECUTED and no entry claims they are. Passing here")
        print("  is never a claim that the analysis is right, in any of the four languages.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
