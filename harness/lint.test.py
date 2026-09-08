"""Controls for lint.py. Stdlib only; run with `python harness/lint.test.py`.

Every rule gets BOTH directions: a file it must flag, and a file it must not. The two false
positives this lint produced on its first CI run are pinned here as negative controls, built from
the exact text that tripped it rather than a paraphrase. A paraphrased fixture has passed in this
project's history while proving nothing.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import json  # noqa: E402
from lint import (  # noqa: E402
    lint_must_appear, lint_sas, lint_stata, strip_hash_comments)

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        FAILURES.append(name)


def write(tmp, name, text):
    p = Path(tmp) / name
    p.write_text(text)
    return p


def main():
    with tempfile.TemporaryDirectory() as tmp:
        print("Stata")

        # NEGATIVE CONTROL, byte-faithful from the file the first CI run wrongly flagged.
        good = write(tmp, "good.do", '''* Conditional logistic regression for a 1:m matched case-control study
* PINNED DEFAULT: clogit reports coefficients unless asked otherwise. The log-odds scale is what
* the harness compares, so no "or" option is used here; add it when reading the output by eye.
import delimited "fixture.csv", clear varnames(1)
clogit case exposed covariate, group(set_id)
''')
        check("a semicolon inside a COMMENT is not flagged", lint_stata(good) == [],
              lint_stata(good))

        bad = write(tmp, "bad.do", '''* a real mistake
clogit case exposed, group(set_id);
''')
        check("a semicolon in CODE is flagged", len(lint_stata(bad)) == 1)

        inline = write(tmp, "inline.do", '''clogit case exposed, group(set_id) // trailing; comment
''')
        check("a semicolon after // is not flagged", lint_stata(inline) == [])

        empty = write(tmp, "empty.do", "* only a comment\n")
        check("a file with no code at all is flagged", len(lint_stata(empty)) >= 1)

        print("SAS")

        # NEGATIVE CONTROL: PROC GENMOD has no event= concept, and the first run flagged it.
        genmod = write(tmp, "genmod.sas", '''/* Modified Poisson */
proc genmod data=rr;
    class id;
    model outcome = exposed covariate / dist=poisson link=log;
    repeated subject=id / type=ind;
run;
''')
        check("PROC GENMOD with dist=poisson is NOT asked for event=",
              lint_sas(genmod) == [], lint_sas(genmod))

        # BUT A BINOMIAL GENMOD HAS EXACTLY THE SAME DEFAULT, and the rule used to exempt it: its
        # scope was written from the Poisson file above and generalised to all of GENMOD. Found
        # 2026-09-08 when the first GENMOD-binomial file arrived; it set event='1' anyway, so
        # nothing would have caught it if it had not.
        genmod_bin_bad = write(tmp, "genmod_bin_bad.sas", '''proc genmod data=d;
    class clinic;
    model outcome = exposed x / dist=binomial link=logit;
    repeated subject=clinic / type=exch;
run;
''')
        check("PROC GENMOD with dist=binomial and no event= IS flagged",
              len(lint_sas(genmod_bin_bad)) == 1, lint_sas(genmod_bin_bad))
        check("and the finding names GENMOD rather than LOGISTIC",
              "GENMOD" in (lint_sas(genmod_bin_bad) or [""])[0])

        genmod_bin_ok = write(tmp, "genmod_bin_ok.sas", '''proc genmod data=d;
    class clinic;
    model outcome(event=\'1\') = exposed x / dist=binomial link=logit;
    repeated subject=clinic / type=exch;
run;
''')
        check("PROC GENMOD with dist=binomial and event= is not flagged",
              lint_sas(genmod_bin_ok) == [], lint_sas(genmod_bin_ok))

        # AND THE RULE IS PER STEP. The old version tested every model statement in the file as
        # soon as one PROC LOGISTIC appeared anywhere in it, so this correct pairing was flagged
        # for the Poisson step's statement.
        mixed = write(tmp, "mixed.sas", '''proc logistic data=d;
    model case(event=\'1\') = exposed;
run;

proc genmod data=d;
    model count = exposed / dist=poisson link=log offset=logpt;
run;
''')
        check("a correct LOGISTIC step beside a Poisson GENMOD step is not flagged",
              lint_sas(mixed) == [], lint_sas(mixed))

        logistic_bad = write(tmp, "logistic_bad.sas", '''proc logistic data=d;
    strata set_id;
    model case = exposed covariate;
run;
''')
        check("PROC LOGISTIC without event= IS flagged", len(lint_sas(logistic_bad)) == 1)

        logistic_ok = write(tmp, "logistic_ok.sas", '''proc logistic data=d;
    strata set_id;
    model case(event='1') = exposed covariate;
run;
''')
        check("PROC LOGISTIC with event= is not flagged", lint_sas(logistic_ok) == [],
              lint_sas(logistic_ok))

        norun = write(tmp, "norun.sas", '''proc genmod data=d;
    model y = x / dist=poisson link=log;
''')
        check("a SAS file with no run; is flagged", len(lint_sas(norun)) == 1)

        commented = write(tmp, "commented.sas", '''/* proc logistic data=d; model y = x; */
proc genmod data=d;
    model y = x / dist=poisson link=log;
run;
''')
        check("a PROC LOGISTIC inside a COMMENT does not trigger the event= rule",
              lint_sas(commented) == [], lint_sas(commented))

        print("comment stripping (R and Python)")

        # A `#` inside a string is not a comment. A regex-based stripper deletes the rest of the
        # line here, and `must_appear` would then report a string it can plainly see as absent.
        r_hash = 'sep <- "#"\nfit <- coxph(Surv(time, event) ~ exposed, ties = "efron")\n'
        check("a # inside an R string is not treated as a comment",
              'ties = "efron"' in strip_hash_comments(r_hash))
        check("a real R comment IS stripped",
              "efron" not in strip_hash_comments('fit <- lm(y ~ x)  # ties = "efron"\n'))

        # A PYTHON DOCSTRING IS PROSE, and is dropped. This test asserted the opposite until
        # 2026-09-08, when a python.py declared cov_struct=Exchangeable() in must_appear, wrote it
        # in its module docstring, called the constructor a different way in the code, and PASSED.
        # That is the "described but not set" case the check names as the more dangerous of the
        # two -- available in the one language whose convention is to describe things in a string.
        py_doc = '''"""Docstring mentioning # and cov_type="HC3" in prose."""
res = mod.fit(cov_type="HC1")
'''
        stripped = strip_hash_comments(py_doc, triple=True)
        check("a Python docstring's contents are DROPPED, like the comment they are",
              'cov_type="HC3"' not in stripped)
        check("code after a docstring containing a # survives it",
              'cov_type="HC1"' in stripped)
        check("an ordinary Python string literal is CODE and is kept",
              "cov_type='naive'" in strip_hash_comments(
                  "se = fit.standard_errors(cov_type='naive')\n", triple=True))
        check("a real Python comment IS stripped",
              "HC3" not in strip_hash_comments('res = mod.fit()  # HC3 would go here\n',
                                               triple=True))
        # BOTH DIRECTIONS on the real case: the same file, the option in the docstring only,
        # against the same file with it in the call.
        only_prose = '''"""Uses cov_struct=Exchangeable() throughout."""
model = sm.GEE(y, X, groups=g, cov_struct=Independence())
'''
        in_code = '''"""Uses an exchangeable working correlation."""
model = sm.GEE(y, X, groups=g, cov_struct=Exchangeable())
'''
        check("an option present only in the docstring is NOT code",
              "cov_struct=Exchangeable()" not in strip_hash_comments(only_prose, triple=True))
        check("the same option in the call IS code",
              "cov_struct=Exchangeable()" in strip_hash_comments(in_code, triple=True))

        print("must_appear")

        def entry(name, expected, files):
            d = Path(tmp) / name
            d.mkdir()
            (d / "expected.json").write_text(json.dumps(expected))
            for fn, body in files.items():
                (d / fn).write_text(body)
            return d

        SAS_OK = ("/* PINNED: ties=efron, because PROC PHREG defaults to Breslow. */\n"
                  "proc phreg data=surv;\n"
                  "    model time*event(0) = exposed / ties=efron;\n"
                  "run;\n")
        # The SAME file with the option deleted from the statement and left in the comment above
        # it. This is byte-identical to SAS_OK apart from that deletion, which is the point: a
        # substring search over the raw text cannot tell these two apart and calls both a pass.
        SAS_COMMENT_ONLY = SAS_OK.replace(" / ties=efron;", ";")

        good = entry("good", {"must_appear": {"sas": ["proc phreg", "ties=efron"]}},
                     {"sas.sas": SAS_OK})
        check("a file containing every declared string passes", lint_must_appear(good) == [],
              lint_must_appear(good))

        comment_only = entry("comment_only", {"must_appear": {"sas": ["ties=efron"]}},
                             {"sas.sas": SAS_COMMENT_ONLY})
        probs = lint_must_appear(comment_only)
        check("a default named ONLY in a comment is flagged", len(probs) == 1, probs)
        check("and the message says which of the two mistakes it is",
              probs and "only in a comment" in probs[0], probs)

        gone = entry("gone", {"must_appear": {"sas": ["ties=efron"]}},
                     {"sas.sas": "proc phreg data=surv;\n    model t*e(0) = x;\nrun;\n"})
        probs = lint_must_appear(gone)
        check("a declared string absent altogether is flagged", len(probs) == 1, probs)
        check("and is reported as absent rather than as a comment",
              probs and "absent" in probs[0], probs)

        # SAS is case-insensitive as a language; the declaration must not depend on how the file
        # happens to be typed.
        shouty = entry("shouty", {"must_appear": {"sas": ["proc phreg", "ties=efron"]}},
                       {"sas.sas": SAS_OK.upper()})
        check("a declaration matches SAS written in upper case", lint_must_appear(shouty) == [],
              lint_must_appear(shouty))

        # The other direction: a rule that only checks what it was handed asserts its own scope.
        undeclared = entry("undeclared", {"must_appear": {"r": ["coxph("]}},
                           {"r.R": "fit <- coxph(Surv(t, e) ~ x)\n", "stata.do": "stcox x, efron\n"})
        probs = lint_must_appear(undeclared)
        check("a language file that declares NOTHING is flagged", len(probs) == 1, probs)
        check("and the finding names the undeclared language",
              probs and "stata" in probs[0], probs)

        ghost = entry("ghost", {"must_appear": {"sas": ["proc phreg"]}},
                      {"r.R": "fit <- coxph(Surv(t, e) ~ x)  # no sas.sas beside it\n"})
        probs = lint_must_appear(ghost)
        check("declaring a language whose file is missing is flagged",
              any("does not exist" in p for p in probs), probs)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} control(s) failed")
        return 1
    print("all controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
