# Study plan: Product Data Readiness for AI Shopping Agents

This is the study plan for *Can Machines Read the Store? Completeness and Validity of Web Product Data for AI Shopping Agents* (Senthil Kumar Muthu). The hypotheses, measures, pass marks and analyses below were written down and locked on November 20, 2026, after the pilot and before the main measurement. Every change made after the plan was written is logged in the deviation log at the end, with its reason and its effect on the claims.

This public copy keeps the research questions, hypotheses, data and sampling rules, measures, probe design, analysis plan, known limits and deviation log as written. The working copy also held a status tracker, literature notes, journal choice, a timeline, a results summary, cleanup notes and notes about the author's employment; those are omitted here, and section numbers differ from the working copy.

## 1. Purpose and research questions

I want to find out whether the product data stores publish for machines is good enough for an AI shopping agent to rely on. Agents read schema.org Product and Offer markup to learn a product's price, availability and identity. Adoption of that markup is well counted. How complete and correct each record is hasn't been measured at web scale since 2020.

- **RQ1. Completeness.** What share of product records carry the fields an agent needs: name, price with currency, availability, a global identifier (GTIN or MPN), brand, image, and shipping or return terms?
- **RQ2. Validity and consistency.** How often are those fields wrong on their face: an invalid GTIN check digit, a currency that isn't an ISO 4217 code, availability outside the schema.org list, a price that doesn't parse, a price that has expired by the crawl date, or two offers on one page with conflicting prices?
- **RQ3. Change, catalog size and format.** How did completeness change between an earlier and the latest release, and does completeness differ by catalog size and by markup format?
- **RQ4. Does it matter to an agent? (secondary)** When a specific field is missing or wrong, how often does an LLM assistant answer a question about that field incorrectly?

The answers feed one practical output: an agent-ready product data profile that says which fields a store must publish, and how, before an agent can trust it (section 8).

## 2. Hypotheses

Each hypothesis is tested on the main sample only, after the pilot. Thresholds are fixed here, before any full run, and every result is reported as measured.

| ID | Hypothesis | Supported if |
| --- | --- | --- |
| H1 | Most product records can't answer an agent's three basic questions: what it costs, whether it's in stock, and exactly which product it is | Under 50% of records carry a parseable price with a valid currency, a schema.org availability value and a valid GTIN or an MPN with brand, with the 95% interval wholly under 50% |
| H2 | Where identifiers appear, a meaningful share are invalid | At least 5% of GTIN values fail the length or check-digit test, with the interval excluding 5% |
| H3 | Larger catalogs publish more complete records than small ones | The site-level core-field rate is at least 10 points higher for sites with over 1,000 records than for sites with 2 to 10 records, with the interval of the difference excluding zero |
| H3b | JSON-LD records are more complete than Microdata records | The core-field rate is at least 5 points higher for JSON-LD records, with the interval of the difference excluding zero. Microdata records are identified by WDC's microdata item marker; all others are treated as JSON-LD |
| H4 | Completeness improved over time | The core-field rate is higher in the later release than the earlier one, with the interval of the difference excluding zero |
| H5 | Missing or wrong fields change what an LLM assistant answers (secondary) | For price, availability and identity questions, accuracy drops by at least 20 points when that field is removed from an otherwise complete record, in both models tested |

The unit is the product record. Site-level versions of H1 to H4 are reported beside them, so a few very large sites can't drive the result.

## 3. Data and ethics rules

The study uses only public Web Data Commons (WDC) extractions of schema.org markup from the Common Crawl, used under the Common Crawl Terms of Use. Nothing comes from inside any company.

| Dataset | Use | Notes |
| --- | --- | --- |
| WDC schema.org Product subset, December 2024 release | Main measurement | Latest confirmed release. If a newer release is out at data access, I'll use it and log the change |
| WDC Product subset, December 2022 release | Trend comparison (H4) | Two years earlier; same pipeline and rules. The 2021 Product directory isn't publicly listable |
| Pinned LLMs, run locally where possible | Secondary probe (H5) | Model names and versions fixed in the pilot |

**Sampling.** WDC splits each Product subset into part files, and all records from one pay-level domain sit in the same file. A random draw of files is therefore a cluster sample of sites, and the intervals resample sites. With seed 20261120 I drew 15 of the 1,658 files in the 2024-12 release: parts 217, 258, 274, 284, 436, 601, 632, 791, 855, 869, 908, 1063, 1197, 1456 and 1472. With seed 20261121 I drew 3 of the 179 files in the 2022-12 release: parts 44, 71 and 134. If the 2024-12 draw holds fewer than 1 million records or 50,000 sites, I'll draw more files with seed 20261122 and log it.

**Ethics and safeguards.**

- Only product data that stores published for machines. No personal data is loaded; Person, Review author and similar fields are dropped at parse time.
- No raw data is redistributed. I'll release code and aggregate results only.
- No website or retailer is named in the paper. Results are reported in aggregate, by size band and top-level domain.

## 4. Measures

The unit is a product record: one schema.org Product on one page, with its offers. Each field is scored present and, where it can be checked, valid.

| Field | Present if | Valid if |
| --- | --- | --- |
| Name | Non-empty `name` | Not a placeholder or a URL |
| Price | `price` on an Offer or its PriceSpecification | Parses as a positive number |
| Currency | `priceCurrency` present | A current ISO 4217 code |
| Availability | `availability` present | Maps to a schema.org ItemAvailability value (http, https or short form accepted; a strict rate is reported too) |
| Global identifier | Any `gtin`, `gtin8`, `gtin12`, `gtin13`, `gtin14`, or `mpn` with `brand` | A GTIN has a legal length and a correct GS1 check digit |
| Brand, image, description, SKU | Non-empty | Not checked |
| Shipping terms | `shippingDetails` on the Offer | Has a rate or a delivery time |
| Return terms | `hasMerchantReturnPolicy` | Has a return window or a policy category |
| Price date | `priceValidUntil` | Not earlier than the crawl month |

**Composite measures.**

- **Core-field rate:** the share of records with a valid price, currency, availability and global identifier. These answer an agent's three basic questions: cost, stock and identity. H1, H3 and H4 use it.
- **Conflict rate:** the share of pages where two offers for the same SKU or GTIN give different prices with no price type to tell them apart.
- **Site readiness:** the share of sites where at least 90% of records pass the core-field test.

The pilot freezes the parsing rules and the placeholder list before the main run.

## 5. Secondary LLM probe

The probe asks one narrow question: when a field is missing or wrong, does an assistant answer a question about that field wrongly? It's secondary, and it's reported as measured, even if the effect is small or null.

**Records.** 600 records drawn from the main sample that pass every core field, stratified by size band. Their own values are the ground truth.

**Conditions.** Each record is shown to the model as its JSON-LD in five forms:

1. Complete, as published.
2. Price removed.
3. Availability removed.
4. Global identifier removed.
5. Availability made inconsistent: a second offer for the same SKU says out of stock while the first says in stock.

**Questions.** Fixed templates: "What does this cost, in what currency?", "Can I buy this today?", "What is this product's GTIN or manufacturer part number?" Answers are scored right, wrong or abstained. An abstention counts as correct when the field is missing, since that's the safe behavior.

**Models.** Two pinned models, at least one open-weight and run locally, with the prompt saved in the code. H5 is supported only if both models show the drop.

## 6. Analysis plan

The main results are field-by-field rates with 95% intervals, the core-field rate, and its change between releases.

1. **Intervals.** 1,000-resample bootstrap over sites, so large sites can't narrow the intervals unfairly.
2. **Record and site views.** Every rate is reported per record and per site (the mean of site rates).
3. **Breakdowns.** By site size band (1, 2 to 10, 11 to 100, 101 to 1,000, over 1,000 records), and by top-level domain group.
4. **Format.** WDC merges the formats in one Product subset, but Microdata items carry a microdata item marker, which the pilot confirmed. H3b compares records with that marker against all others.
5. **H4.** The same pipeline and rules run on both releases. I'll also report the change for sites present in both, so turnover in the crawl can't create a trend.
6. **H5.** Accuracy by condition and model, with exact binomial intervals, and the paired drop from the complete condition.
7. **Sensitivity.** Lenient versus strict availability parsing, GTIN-only versus GTIN-or-MPN identity, and a 1-in-10 subsample of the largest sites.

Anything outside this list is exploratory and labelled that way in the paper.

## 7. Contribution: agent-ready product data profile

The paper ends with a design contribution: a minimum data contract a store must publish before an agent can quote, stock-check and identify a product without guessing.

- **Tiers.** A *core* tier (valid price, currency, availability and global identifier), a *transaction* tier (shipping and return terms, price validity date), and a *comparison* tier (brand, condition, rating).
- **Rules from the evidence.** Each rule cites the measured failure it prevents, such as the GTIN check-digit rate or the offer-conflict rate. Rules with no measured failure behind them stay out.
- **Checks a platform can run.** Each tier is written as machine-checkable conditions, released with the code as a validator anyone can run on their own markup.

## 8. Known limits

| Limit | Why it matters | What I do about it |
| --- | --- | --- |
| Common Crawl isn't the whole web | Large retailers increasingly block its crawler, so big stores may be under-represented | Report coverage by size band; claim results for the crawled web only |
| Markup isn't everything an agent reads | Agents also use merchant feeds, APIs and page text | Scope the claim to on-page markup |
| The crawl is a snapshot | A price or stock value may have been right when crawled | Validity tests are internal (check digits, codes, conflicts) |
| Parser errors in the extraction | Some failures may be WDC's, not the store's | Hand-check 200 random failing records in the pilot and report the share caused by extraction |
| The LLM probe is controlled, not live | Real agents may cross-check other sources | Label it secondary; report it as measured |

## 9. Deviation log

Any change after the plan was first written gets a row here and a sentence in the paper. Rows marked pre-lock were made before the hypotheses and thresholds were locked; rows marked post-lock were made after.

| Date | Change | Reason | Effect on claims |
| --- | --- | --- | --- |
| Nov 20, 2026 (pre-lock) | Scope narrowed to a measurement-first paper; LLM probe made secondary; agent-ready profile added | An independent second review flagged scope creep | Fewer claims; one design contribution |
| Nov 20, 2026 (pre-lock) | Positioned against Steiner, Peeters and Bizer (WWW 2026) and Volpini et al. (2026) | Found in the prior-art check | Novelty claim limited to record-level quality at web scale |
| Nov 20, 2026 (pre-lock) | H3 changed from JSON-LD versus Microdata to catalog size; trend release moved from 2021-12 to 2022-12; file draw fixed by seed | WDC merges the two formats in the Product subset and groups files by site; the 2021-12 Product directory isn't publicly listable | No format claim; the trend spans two years, not three |
| Nov 20, 2026 (pilot, pre-lock) | Parsing rules frozen: offers followed whether written as blank nodes or IRIs; variants inherit brand, identifiers and return policy from their ProductGroup; property names matched case-sensitively, with case-forgiving matching as a sensitivity check; price 0 is invalid; nested products kept and flagged | Pilot on part 217 (350,917 records, 2,332 sites). The 200-record hand-check found no remaining parser misses once these rules were in: failures came from the stores' markup (empty or malformed GTINs, MPN without brand, price 0, the retired code RUR, capitalised property names, fields only on unrelated items) | Case-forgiving matching moves the core-field rate by about one point |
| Nov 20, 2026 (pilot, pre-lock) | Part 217 removed from the confirmatory sample; 10 more 2024-12 files drawn with seed 20261122: parts 74, 127, 492, 795, 1045, 1178, 1276, 1295, 1299 and 1381 | I saw the pilot file's core-field rate, which bears on H1. About 2,300 sites per file meant 15 files would fall short of the 50,000-site floor | Hypotheses are tested on 24 files I hadn't looked at |
| Nov 20, 2026 (pre-lock) | Format comparison restored as H3b beside catalog size (H3). Plan locked after this row | The pilot showed Microdata items are marked in the data, so the format can be measured after all | One more hypothesis; any later change is a post-lock deviation |
| Nov 20, 2026 (post-lock) | Two more 2024-12 files drawn with seed 20261123 (parts 1198 and 1570) | The 24 files held 48,314 sites, under the 50,000 floor | Final 2024 sample: 26 files, 8,477,442 records, 51,382 sites |
| Nov 20, 2026 (post-lock) | 2022-12 treated as a sample of records, not of whole sites; site-level measures and size bands use 2024 only | Unlike 2024, the 2022 files aren't grouped by site: 298,643 of 995,398 sites appear in more than one file | H4 is a record-level comparison, which the change doesn't affect; the sites-in-both check is reported beside it |
| Nov 20, 2026 (post-lock) | Site bootstrap run with Poisson weights (1,000 draws) for record-level rates; size-band and H3 intervals use ordinary resampling of sites | Ordinary resampling of a million 2022 sites didn't fit the machine's run limits; the Poisson bootstrap is a standard large-sample equivalent | None expected; same estimator, same unit of resampling |
| Nov 20, 2026 (post-lock, before the probe ran) | Probe models: Llama 3.2 3B and Qwen 2.5 3B, both open-weight, run locally through Ollama at temperature 0 with a fixed seed; model digests recorded. Each condition asks only the question it tests (the complete record gets all three). Answers are requested as JSON with null meaning 'not stated'. Records come from the seeded reserve of complete top-level 2024 records, one per site, spread across size bands. Descriptions are cut to 300 characters and image lists to one URL. Condition 5 is scored correct only when the model returns null | The only machine available has 8 GB of memory and no paid model access; asking the targeted question keeps the run to about 4,200 prompts per model | H5 claims cover small open models only; the limitations section says so |
| Nov 21, 2026 (during the probe) | Answer length capped at 256 tokens for the last 93 Qwen prompts | One prompt made Qwen generate until the 10-minute timeout, three times | None: the longest answer from either model was 137 characters |
| Nov 21, 2026 (scoring) | Number parser fixed to read scientific notation (e.g. 4.499E1); probe answer key rebuilt; the old key is kept as probe_truth_v1_bad_sci_notation.json | WDC stores numeric JSON-LD prices as xsd:double in scientific notation. The parser dropped the exponent, so 162 of 600 probe records had a wrong expected price | Probe price scores corrected. Main-study validity rates are unaffected (any positive number passed either way); re-run on Nov 21 with the fixed parser: price validity rose by under 0.1 point, the conflict rate stayed at 1.3%, and every hypothesis result and interval held (H3's lower bound moved from 13.0 to 13.1) |
| Nov 21, 2026 (scoring) | Probe limitation recorded: 162 records showed the models WDC's scientific-notation price, not the decimal the store published | My rendering of the records passed the extraction format through unchanged | Complete-record price accuracy is reported on the 438 plain-format records as the clean estimate; H5's price outcome doesn't depend on it |
