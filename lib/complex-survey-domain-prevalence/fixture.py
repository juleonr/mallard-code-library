"""Stratified one-stage PSU sample, complete enumeration within each sampled PSU.
Weights are inverse PSU inclusion probabilities; the variance uses a with-replacement
approximation (no FPC), appropriate only when the sampling fractions are negligible.
"""
import csv
import random


def rows(seed=717, m=30):
    rng = random.Random(seed)
    # Equal cluster sizes; independent stratum risks. Domain is unrelated to the outcome.
    for h, population_psus, risk in [(1, 3000, .15), (2, 6000, .35), (3, 12000, .60)]:
        for psu in range(1, m+1):
            cluster_risk = min(.98, max(.02, risk + rng.uniform(-.10, .10)))
            in_domain = rng.random() < .6
            for _ in range(20):
                yield dict(stratum=h, psu=psu, weight=population_psus/m,
                           domain=int(in_domain and rng.random() < .7),
                           outcome=int(rng.random() < cluster_risk))


if __name__ == "__main__":
    with open("fixture.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=["stratum", "psu", "weight", "domain", "outcome"])
        writer.writeheader()
        writer.writerows(rows())
