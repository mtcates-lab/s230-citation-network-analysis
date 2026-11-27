# Research design

## 1. Opinion corpus

**Inclusion criteria.** Include operative, published opinions issued by a U.S. court of appeals or the U.S. Supreme Court from November 12, 1997, through December 31, 2025. The court must interpret, apply, limit, or distinguish § 230(c)(1), (c)(2), (e), or (f) in controlling reasoning that materially resolves a contested claim, defense, or issue. Procedural rulings and decisions on statutory scope, exceptions, or preemption qualify when they meet that standard. Apply the same rule to statutory reasoning in a constitutional dispute.

**Exclusion criteria.** Exclude state and district court opinions, unpublished opinions, and vacated opinions. Use the operative published version when an opinion has been superseded. Exclude opinions when § 230 appears only in passing, as policy background or definitional borrowing, in a party’s argument or an unreviewed lower-court ruling, in dicta, in discussion of a reserved or forfeited issue, on an assumption, or as an independently sufficient alternative ground.

Record the issue, posture, statutory result, appellate disposition, and controlling evidence separately. Record statutory scope determinations separately from claim-level immunity results.

## 2. Case discovery

The documented CourtListener search used four expressions for § 230, a precedential filter, a federal appellate court list, and a lower filing-date parameter of January 1, 1996. The recorded request had no upper date limit. The bundled export holds 217 records, of which 207 have listed filing dates inside the study window. Candidate records can represent duplicate versions or ineligible opinions. Outcome and network results use the screened opinion table.

The Python run generates a crosswalk to the inclusion table by exact cluster ID and then by matching court, date, and exact reporter. Nonmatches retain same-court/date leads where applicable. A mechanical nonmatch has no legal exclusion code. The crosswalk can be used to reconcile independently retrieved candidates, publication status, and subsequent treatment. CourtListener match counts describe overlap with the discovery export. The separate [Shepard’s coverage audit](validation/lexis_coverage.md) identifies 56 eligible operative opinions in the captured appellate records. The release includes all 56.

## 3. Graph construction

The unit is a directed, unweighted opinion pair. Orient each edge from the citing opinion to the cited opinion. Consecutive passages, repeated mentions, and reporter aliases can support one edge. Retain isolates. The input checks compare the passage-derived edges to the coded pair decisions and require a strictly earlier decision date at each target. This uses the best recorded operative decision date for each opinion family. The passage table retains the actual cited reporter where available.

| Graph | Inclusion rule |
| --- | --- |
| Baseline | One pair when at least one audited passage is coded as the court’s own discussion |
| § 230 reasoning | One pair when at least one audited court passage materially supports § 230 reasoning |
| § 230(c)(1) comparison | Induce both graphs on the 43 opinions deciding a publisher or third-party-source issue. Keep mixed outcomes and *Batzel*, whose scope ruling qualifies despite the remand |
| Resolved § 230(c)(1) sensitivity | Limit those graphs to the 42 opinions with a claim-level result under the comparison rule |
| *Perfect 10* add-back | Add the operative *Perfect 10* opinion to the 43-opinion scope |
| Reporter and boundary checks | Use exact full-reporter matches in baseline passages, or omit *StubHub* and *Erie* from the baseline |

The coding tracks court discussion, reports of party or lower-court arguments, source artifacts, and selected citations to separate writings. The opinion-boundary table identifies the controlling-text window and first separate-opinion boundary for every included opinion. Every retained edge has support within those windows. Shared-line delimiters separate majority text from a following concurrence or dissent. Opinion part and citation voice remain separate codes. Eleven selected external passages remain in the passage ledger and generate no edges between included opinions.

## 4. Outcomes and interpretation

For the primary § 230(c)(1) outcome comparison, include an issue when the appellate court decides whether publisher treatment or third-party source bars an underlying claim or theory of liability. Use B for barred and N for a rejected defense on that issue. Count the statutory ruling separately from the appeal’s disposition. A pleading-stage, summary-judgment, or injunction-stage ruling qualifies when it resolves the § 230 defense to an identified liability theory at that stage. When the court determines the enforceability of a law in a preemption challenge, answers a certification question without deciding claim-level liability, or announces a standard and leaves applicability for remand, keep the determination outside the primary resolved denominator.

Aggregate B and N codes by opinion. The three resolved categories are all barred, none barred, and mixed. The denominator includes each mixed opinion once. The broader sensitivity also counts a controlling § 230(e)(3) determination turning on § 230(c)(1) publisher treatment or third-party source. Code B if § 230 forecloses enforcement of the disputed duty in the application before the court and N if it does not. Screen the recorded issues for all 56 included opinions for this rule. *StubHub*, *HomeAway*, and *Paxton* supply the three additional determinations. [The case comparison](data/publisher_outcome_comparison.csv) shows the issue and locator for each added ruling. The graph comparisons continue to use their documented node sets.

Use opinion date for the April 11, 2018 split. Tabulate direct carveout cases and publisher-threshold cases separately. Show equal-length windows and the post-enactment count after excluding opinions that directly decided the carveout. The period comparison is descriptive. Questions presented, posture, courts, and the selection of cases can vary by period.

PageRank measures citation prominence in a specified graph. Assess its rank and score against simulations that keep the set of earlier eligible targets and each citing opinion’s outgoing citation count. Binding effect depends on the opinion and forum. Compare the Leiden reference, consensus, and directed partitions as summaries of citation structure. Use the controlling passages to interpret individual links within a group. Circuit divergence describes differences between distributions of cited opinions. Comparisons over time require circuit pairs that meet the same thresholds in each period. A doctrinal conflict requires comparable holdings.

## 5. Source validation

The validation tables identify the opinion copies in `sources/`, the controlling-text windows, and the separate-opinion delimiters. Each retained edge has at least one supporting passage within the controlling text. The passage table preserves the printed citation, the matched opinion, and its context. The source artifacts remain excluded.

Reporter aliases connect earlier reporters to the operative opinion family. Citation parsing identifies candidate references; graph construction uses the coded passage flags. Short-form detection does not establish exhaustive recall for bare names, *Id.*, *supra*, or references outside the selected patterns.

The candidate-screening table settles all 217 records with Include, Exclude, or Duplicate decisions and case-specific evidence. Corrected dates and reporters occupy separate fields; original export fields remain unchanged. The original discovery route for the Fifth Circuit Paxton opinion is unavailable. Its verified preemption holding supports inclusion, and the provenance table identifies the court source. These decisions settle the supplied candidate set; they do not establish exhaustive coverage of all eligible opinions.
