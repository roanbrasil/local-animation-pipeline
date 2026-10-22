"""Summarize clips/timings.csv from one or more machines.

  python bench_summary.py mac/timings.csv spark/timings.csv pc4090/timings.csv
"""
import csv
import sys
from collections import defaultdict

rows = defaultdict(list)
for path in sys.argv[1:] or ["clips/timings.csv"]:
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows[(r["machine"], r["backend"])].append(r)

print(f"{'machine':<22}{'backend':<8}{'clips':>6}{'video s':>9}"
      f"{'wall min':>10}{'s per video s':>15}")
for (machine, backend), rs in sorted(rows.items()):
    video = sum(float(r["clip_s"]) for r in rs)
    wall = sum(float(r["wall_s"]) for r in rs)
    print(f"{machine:<22}{backend:<8}{len(rs):>6}{video:>9.1f}"
          f"{wall / 60:>10.1f}{wall / video:>15.1f}")
