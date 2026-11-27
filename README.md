# Can Machines Read the Store? Code and data

Code, aggregate results and validator for:

> Muthu, S. K. (2026). *Can Machines Read the Store? Completeness and Validity of Web Product Data for AI Shopping Agents.* Manuscript under review.

To cite this code and data, use the Zenodo DOI shown in the repository's release (see `CITATION.cff`).

The study measures how often schema.org product markup on the public web lets an AI shopping agent answer three questions: what an item costs, whether it's in stock, and exactly which item it is. It uses the Web Data Commons (WDC) schema.org Product subsets for December 2024 and December 2022.

## What's here

| Folder | Contents |
|---|---|
| `validator/` | `agent_ready_validator.py`: checks a page's JSON-LD against the agent-ready product data profile (core, transaction and comparison tiers). Standard library only. |
| `code/` | The measurement pipeline: parsing (`parse.py`), field rules (`measure.py`), per-site aggregation (`agg.py`, `run2.sh`), the pilot hand-check (`check200.py`), bootstrap draws (`boot.py`) and hypothesis tests (`analyze_lib.py`, `analyze2.py`). |
| `probe/` | The language-model probe: building the 600-record probe set (`../code/build_probe.py`), running it against local models (`run_probe.py`), scoring (`score_probe.py`), per-item scores (`probe_scored.csv`), model digests and settings (`model_versions.json`) and summary results (`probe_results.json`). |
| `results/` | Per-site aggregate counts for each release (`site_aggregates_*.csv.gz`) and all hypothesis results with intervals (`hypothesis_results.json`). |
| `scripts/` | `export_aggregates.py`, which produced the released aggregate files, and `reproduce_from_csv.py`, which recomputes the headline numbers from them. |
| `STUDY_PLAN.md` | The study plan (research questions, hypotheses, pass marks, measures and analyses), locked before the main measurement, with the log of every later change. |
| `SAMPLING.md` | Every WDC file in the sample, the seeds used to draw them, and the pilot file excluded from the confirmatory sample. |

## Check your own markup

```
python3 validator/agent_ready_validator.py your-product-page.html
python3 validator/agent_ready_validator.py product.jsonld --json
```

The validator reads every `<script type="application/ld+json">` block in an HTML file, or a JSON-LD file directly, and reports each rule as passed or failed for every Product it finds.

## Reproduce the headline numbers

```
python3 scripts/reproduce_from_csv.py
```

This prints the record and site counts, the core-field rate for each release and the change for sites present in both releases, from the released aggregate files alone.

## Reproduce the full study

1. Download the WDC Product subset files listed in `SAMPLING.md` from `https://data.dws.informatik.uni-mannheim.de/structureddata/<release>/quads/classspecific/Product/`.
2. The 2022 files are large; the study split each into page-aligned chunks of about 1.2 GB of text before parsing. Any split that keeps each page's quads together gives the same results.
3. Run `code/run2.sh <outdir> <release> <files...>` to parse and aggregate, then `code/boot.py` and `code/analyze2.py` for the tests. The scripts expect to run from one working folder; adjust the paths at the top of `run2.sh` and `agg.py` to your setup.
4. For the probe, run `code/build_probe.py` on the 2024 aggregates to rebuild the 600 records, then `probe/run_probe.py <model>` with Ollama and `probe/score_probe.py`.

Python 3.10 or later. The analysis scripts need NumPy; the parser, probe and validator use the standard library only.

## What isn't here, and why

- **Raw data.** The WDC data is public and stays with WDC under the Common Crawl terms of use. It isn't redistributed here.
- **Website names.** Each site appears under a keyed pseudonym (`site_id`), the same in both releases, with its top-level domain. The key isn't published, so the aggregates don't name any website or retailer.
- **Probe records and raw answers.** The 600 probe records are copies of store markup, so they aren't redistributed. `code/build_probe.py` rebuilds them from the WDC files with the same seed, and `probe_scored.csv` gives every item's score.

## License

Code: MIT License. Aggregate results and documentation: CC BY 4.0.
