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
"""

import argparse
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
    """SAS comments are /* ... */ blocks and lines beginning with `*` up to the next `;`."""
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


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

    # SCOPED TO PROC LOGISTIC, which is the only proc where this matters. LOGISTIC models the
    # LOWER ordered response value by default, so a 0/1 outcome without event='1' inverts every
    # odds ratio in the output and nothing in the listing says so. GENMOD, GLM and the rest have
    # no such default, and requiring it of them flags correct files.
    if re.search(r"\bproc\s+logistic\b", code, re.I):
        for m in re.finditer(r"\bmodel\b[^;]*;", code, re.I | re.S):
            stmt = m.group(0)
            if "event" not in stmt.lower():
                problems.append(
                    f"{path}: PROC LOGISTIC model statement without event= -- "
                    f"the lower response level is modelled by default and the odds ratios invert")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="lib")
    args = ap.parse_args(argv)

    root = Path(args.root)
    sas = sorted(root.glob("*/*.sas"))
    stata = sorted(root.glob("*/*.do"))

    problems = []
    for p in sas:
        problems += lint_sas(p)
    for p in stata:
        problems += lint_stata(p)

    print(f"SAS files: {len(sas)}   Stata files: {len(stata)}")
    for p in problems:
        print(f"  FAIL {p}")
    if not problems:
        print("  structural lint passed. THESE FILES ARE NOT EXECUTED and no entry claims they are:")
        print("  passing here means the text is well formed, never that the analysis is right.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
