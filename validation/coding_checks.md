# Citation and outcome checks

## Citation sample

The check used the sample of 20 citing opinions in `data/recall_sample.json`. Within their controlling text windows, it compared exact operative reporter searches, parser candidates and recorded short-form leads against the baseline graph. The comparison covered earlier included opinions. The sample contains 127 baseline pairs. Exact reporter searches and the parser each returned 122 pairs within those windows. The short-form ledger supplied leads for 57 pairs. The combined checks flagged no pair outside the baseline. See `citation_sample_checks.csv` for counts by citing opinion.

As a separate boundary check, the parser flagged a citation from Henderson to Batzel that the baseline omits. Henderson cites Batzel in a footnote while describing an argument it expressly leaves open. The exclusion follows the rule for citations in accounts of arguments the court does not resolve.

These checks use search patterns and the recorded lead list. A full citation inventory independently enumerated from the sampled opinions would allow an edge recall estimate. Edge recall and reader agreement remain unmeasured.

## Outcome evidence

Checked all 51 issue records underlying the resolved § 230(c)(1) comparison. Each recorded excerpt appears in its cited working-text range and within the controlling opinion window. The check normalizes casing, punctuation and spacing in the excerpts. See `c1_outcome_source_checks.csv` for the locators.

Reviewed the five mixed outcomes against the controlling passages. Roommates.com distinguishes required answers and matching from free-form comments. Barnes distinguishes negligent undertaking from promissory estoppel. Calise distinguishes noncontract duties from duties created by Meta’s promises. Bride distinguishes product-liability theories from alleged misrepresentations. Doe 1 v. Twitter distinguishes claims based on monitoring or editorial decisions from reporting duties that can operate independently of those functions.

Corrected the opening reporter page for the separate FOSTA issue in Doe 1 v. Twitter to 148 F.4th 635. The scope code and pinpoint range remain as recorded. The before/after comparison contains 23 and 19 resolved opinions, with 17 and 8 all-barred outcomes, respectively. The comparison describes the observed periods.
