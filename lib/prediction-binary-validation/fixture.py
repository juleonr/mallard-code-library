"""Independent validation observations from a fixed, already specified risk model.
No fitting, feature selection, preprocessing or tuning uses this validation sample.
"""
import csv
import math
import random


def rows(seed=90210, n=4000):
    rng = random.Random(seed)
    for _ in range(n):
        # Round beyond the accuracy needed here to discard platform libm tail bits.
        x, z = round(rng.gauss(0, 1), 12), rng.randrange(2)
        lp = -0.8 + 0.9 * x + 0.5 * z
        p = round(1 / (1 + math.exp(-lp)), 12)
        yield {"x": x, "z": z, "predicted": p, "outcome": int(rng.random() < p)}


if __name__ == "__main__":
    with open("fixture.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=["x", "z", "predicted", "outcome"])
        writer.writeheader()
        writer.writerows(rows())
