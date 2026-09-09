"""The typed IPTW variant must describe the weights the actual engines compute."""
from contextlib import chdir, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import numpy as np

ENTRY = Path(__file__).resolve().parent.parent / "lib/iptw-propensity-weights-robust-se"
VARIANT = ["ATE-stabilized-untrimmed-HC0"]


def check_entry(path):
    meta = json.loads((path / "meta.json").read_text())
    assert meta["compatibility"]["variant"] == VARIANT, "IPTW scope must declare stabilization"
    with chdir(path), redirect_stdout(io.StringIO()):
        actual = runpy.run_path("python.py")
    treated = actual["d"]["treated"].to_numpy() == 1
    propensity = np.asarray(actual["e"])
    observed_probability = np.where(treated, propensity, 1 - propensity)
    # Stabilized weight × propensity for the observed arm = that arm's marginal probability.
    numerator = np.where(treated, treated.mean(), 1 - treated.mean())
    np.testing.assert_allclose(actual["w"] * observed_probability, numerator, rtol=0, atol=1e-10)
    r = '''source("r.R")
      observed_probability <- ifelse(d$treated == 1, e, 1-e)
      numerator <- ifelse(d$treated == 1, mean(d$treated), 1-mean(d$treated))
      stopifnot(max(abs(w * observed_probability - numerator)) < 1e-10)
    '''
    result = subprocess.run(["Rscript", "-e", r], cwd=path, capture_output=True, text=True)
    assert result.returncode == 0, f"R weight identity check failed:\n{result.stdout}\n{result.stderr}"


check_entry(ENTRY)  # Exact committed fixture and implementations, no paraphrased negative control.
print("PASS declared stabilized variant agrees with executed R and Python weights")
for case in ("old-variant", "python-unstabilized", "r-unstabilized"):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "entry"
        shutil.copytree(ENTRY, path)
        if case == "old-variant":
            target = path / "meta.json"
            meta = json.loads(target.read_text())
            meta["compatibility"]["variant"] = ["ATE-unstabilized-untrimmed-HC0"]
            target.write_text(json.dumps(meta))
        else:
            target = path / ("python.py" if case.startswith("python") else "r.R")
            source = target.read_text()
            before = ("p_treat / e, (1.0 - p_treat) / (1.0 - e)" if case.startswith("python")
                      else "p_treat / e, (1 - p_treat) / (1 - e)")
            assert source.count(before) == 1
            target.write_text(source.replace(before, "1 / e, 1 / (1 - e)"))
        try:
            check_entry(path)
        except (AssertionError, subprocess.CalledProcessError):
            print(f"PASS {case} detected")
        else:
            raise AssertionError(f"{case} escaped the weight/scope consistency check")
