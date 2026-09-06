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
from lint import lint_sas, lint_stata  # noqa: E402

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
        check("PROC GENMOD is NOT asked for event=", lint_sas(genmod) == [], lint_sas(genmod))

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

    print()
    if FAILURES:
        print(f"{len(FAILURES)} control(s) failed")
        return 1
    print("all controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
