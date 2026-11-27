# Shepard’s case coverage

The reference set comes from the U.S. Supreme Court and U.S. courts of appeals sections of the 362-page Shepard’s Comprehensive Report for 47 U.S.C. § 230. With the Federal Courts filter, the report lists 1,426 citing decisions across courts and dates. The comparison uses appellate records within the study window of November 12, 1997 through December 31, 2025.

The report and the screening register identify the same 215 appellate records within that window. Under the study’s inclusion rules, those records comprise 56 eligible operative opinions, 145 exclusions, 12 earlier versions, and two companion orders. [The screening table](lexis_appellate_screening.csv) records these decisions, and [the eligible-opinion table](lexis_eligible_opinions.csv) supplies the reference list.

The dataset includes all 56 eligible opinions in the reference list. Coverage beyond the captured Shepard’s records is unmeasured.

Run the comparison from the repository root.

```bash
python 07_estimate_recall.py case validation/lexis_eligible_opinions.csv --output lexis_case_recall.json
```

The screening table gives opinion or order locators for close exclusions. Where the CourtListener screening ledger documents the same decision, the cluster ID links the Shepard’s row to that evidence. Reporter and publication metadata support straightforward exclusions.
