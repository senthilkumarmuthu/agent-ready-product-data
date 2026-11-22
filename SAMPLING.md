# Sample

All files come from the Web Data Commons schema.org Product subsets:
`https://data.dws.informatik.uni-mannheim.de/structureddata/<release>/quads/classspecific/Product/part_<n>.gz`

Files were drawn with Python's `random.Random(seed).sample(...)`.

## December 2024 (1,658 files; files grouped by pay-level domain)

| Draw | Seed | Files |
|---|---|---|
| First draw (15 of 1,658) | 20261120 | 217, 258, 274, 284, 436, 601, 632, 791, 855, 869, 908, 1063, 1197, 1456, 1472 |
| Second draw (10 more, excluding the first) | 20261122 | 74, 127, 492, 795, 1045, 1178, 1276, 1295, 1299, 1381 |
| Third draw (2 more, excluding both) | 20261123 | 1198, 1570 |

**Pilot file, excluded from the confirmatory sample:** 217. I tested the parser and rules on it and saw its core-field rate before the plan was locked.

**Confirmatory sample:** 26 files (all drawn files except 217): 8,477,442 product records from 51,382 sites.

## December 2022 (179 files; files not grouped by site)

| Draw | Seed | Files |
|---|---|---|
| 3 of 179 | 20261121 | 44, 71, 134 |

**Sample:** 9,362,217 product records. Because the 2022 release isn't grouped by site, it's used only for record-level comparisons.

## Probe

600 records from the seeded reserve of complete, top-level 2024 records (`code/agg.py` keeps up to 100 per file with a seeded reservoir; `code/build_probe.py` shuffles with seed 20261120 and takes one record per site across size bands).
