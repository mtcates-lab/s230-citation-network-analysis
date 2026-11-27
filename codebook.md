# Codebook

## Identifiers and missing fields

`S230-NNN` identifies an operative opinion family. `S230-NNN-INN` identifies an issue within that opinion. `CP-NNNNN` identifies a citation record. IDs are stable across tables. Added opinions receive new identifiers; identifier order does not determine chronology. Dates use ISO 8601 in coded tables. Empty input cells indicate unavailable or inapplicable information. Empty calculated cells indicate an undefined value. Zero is an observed count.

## included_opinions.csv

| Field | Definition |
| --- | --- |
| `opinion_id`, `case_name` | Project identifier and operative caption |
| `circuit`, `decision_date` | Issuing court code and operative date used in the graph |
| `reporter_citation`, `courtlistener_cluster_id` | Operative reporter and recorded CourtListener identifier where available |
| `inclusion_reason`, `screening_pinpoint` | Reason for inclusion and supporting reporter locator |
| `text_source`, `source_lines`, `source_url` | Working source, line range, and location of the opinion copy |
| `primary_graph`, `restricted_c1_graph`, `direct_c1_claim_graph` | Yes/no membership in the full, 43-opinion, and 42-opinion scopes. The analysis checks restricted membership against issue codes |
| `restricted_membership_reason` | Reason for admission to, or exclusion from, the § 230(c)(1) comparison |
| `statutory_claim_outcome`, `c1_claim_outcome` | Opinion-level outcome labels. The analysis derives resolved outcomes from B and N issue rows |
| `appellate_disposition` | What the court did with the appeal |
| `principal_issue_id`, `principal_statutory_ruling`, `number_of_issue_entries` | Main issue, its ruling, and the opinion's issue count |

## data/issues.csv

| Field | Definition |
| --- | --- |
| `issue_id`, `opinion_id`, `subsection` | Issue identifier, parent opinion, and statutory subsection. Historical lettering is retained where applicable |
| `posture_code` | D dismissal-stage coding, P pleadings, S summary judgment, A preliminary or anti-SLAPP ruling, C certification, I interlocutory appeal, J judgment as a matter of law |
| `result_code`, `claim_effect` | B barred, N not barred, S scope/procedure/exception determination, U unresolved or no new determination. Claim effect states the result in words |
| `issue`, `statutory_ruling`, `appellate_disposition` | Question, controlling ruling or issue status, and disposition |
| `reporter_pinpoint`, `source_lines`, `evidence_excerpt`, `pinpoint_type` | Reporter locator, working-text locator, supporting passage, and locator type |
| `ruling_status` | Controlling, reserved, assumed, forfeited, or resolved before this appeal |
| `distinct_c1_issue` | yes for an independently decided publisher or third-party-source issue concerning a liability claim or theory, scope for a decided § 230(c)(1) standard with claim-level application left open, no otherwise. The primary resolved comparison counts B or N on yes rows. |
| `publisher_preemption_effect` | B or N for a controlling § 230(e)(3) enforceability determination that expressly turns on § 230(c)(1) and enters only the broader outcome comparison. Blank on other rows. |

## data/citation_passages.csv

| Field | Definition |
| --- | --- |
| `passage_id`, `citing_opinion_id`, `citing_opinion` | Passage identifier and citing opinion |
| `cited_opinion_id`, `cited_opinion`, `cited_reporter_or_authority` | Target identifier when included, caption or external authority, and reporter or authority identifier |
| `citing_source_line`, `source_locator_file`, `context` | Working-text source line, source label, and surrounding text |
| `citation_as_located`, `match_method`, `location_status` | Printed citation, matching method, and location status |
| `coding_status` | Coded or Excluded source artifact |
| `citation_function` | One primary function for the citation |
| `citing_use` | Court's own discussion, party or lower-court account, or excluded source material |
| `material_to_section_230` | yes when the court passage supports § 230 reasoning, no otherwise |

Citation counts describe the located and coded evidence. An additional *Id.* in the same recorded paragraph can support that passage without adding a counted passage. These counts do not measure every mention of a case.

A rule label supports a governing proposition. Application covers analogy and use on the facts. Distinguishing identifies a material difference or rejects an analogy. Limitation records narrowing or a change in the rule. Statutory history and interpretive rationale can support § 230 reasoning. Background, other issues, arguments merely described, express reservations, and source artifacts have distinct labels. Procedure qualifies when the court uses the cited case in applying § 230.

## data/citation_pairs.csv

| Field | Definition |
| --- | --- |
| `citing_opinion_id`, `citing_opinion`, `cited_opinion_id`, `cited_opinion` | Pair endpoints and captions |
| `number_of_located_passages`, `number_of_coded_passages` | Located-record and coded-record counts for the pair |
| `evidence_for_baseline_graph`, `evidence_for_section_230_graph` | Pair-level flags derived from passage codes |
| `evidence_status`, `citation_functions` | Pair decision and citation functions |
| `passage_ids`, `section_230_support_passages` | Passage identifiers for the pair and its affirmative statutory evidence |

The analysis regenerates pair flags and supporting identifiers in `edge_evidence.csv`.

## data/fosta.csv

`opinion_id` joins to the inclusion table. `question_type` describes pre-amendment context, direct carveout, facial challenge, publisher threshold, or independent duty. `subsection`, `conduct_examined`, `holding`, and `outcome` describe the determination. `reporter_pinpoint` and `authorities` identify supporting evidence. `opinion_date` is checked against the inclusion table.

## Candidate export and screening

The first column of `courtlistener_candidates.tsv` is an unlabeled CourtListener cluster ID. The other columns contain the caption, court, filing date, reporter list, docket, judge, publication status, URL, and excerpt. The crosswalk records mechanical matches and joins the screening fields from `validation/candidate_screening.csv`.

| Screening field | Definition |
| --- | --- |
| `screening_decision` | Include, Exclude, or Duplicate. Exclude can identify an additional version whose operative opinion is already retained |
| `decision_basis`, `decision_reason` | Rule applied and case-specific explanation |
| `retained_opinion_or_candidate` | Retained opinion or candidate identifier |
| `evidence_status` | Whether the decision uses opinion text or metadata |
| `verification_source`, `evidence_file`, `evidence_locator` | Public source, bundled file when available, and supporting location |
| `supporting_passage_or_metadata` | Source excerpt, concise paraphrase, or identified metadata |
| `subsection`, `section_230_result` | Relevant statutory scope and result |
| `verified_decision_date`, `verified_reporter_citation` | Corrected operative metadata when needed to resolve a date, reporter, or version conflict. Original export fields stay unchanged |

Original export fields remain unchanged. A missing bundled evidence file does not remove the public source URL or supporting pinpoint. Mechanical match status is separate from the screening decision: an alias can lack an exact ID match while its eligibility is settled. Dart and Children’s Health Defense are integrated in the opinion, issue, and citation tables.

## Source validation

The tables in `validation/` identify source coverage, citation leads, opinion boundaries, and the passages supporting each edge. The short-form coverage table records parser counts for each opinion. The leads table records potential references and their coding status. These counts do not establish exhaustive citation recall.

Source-line numbers count newline-delimited lines from one in the named text. A shared-line delimiter overrides an inclusive endpoint. The opinion-boundary table identifies the first separate writing; it does not inventory every later separate writing. A majority can use a concurrence or dissent from a cited case in its own reasoning. Opinion part does not override citation voice or materiality.

## Shepard’s validation tables

`lexis_appellate_screening.csv` links each captured in-window appellate record to its earlier screening entry. The case identifiers are the Lexis citation or reporter and decision date. `courtlistener_screening_cluster_id`, when populated, joins directly to the evidence in `validation/candidate_screening.csv`. `screening_decision` reports eligibility under the release rules. `corpus_opinion_id` identifies an exact reporter match in the release. `lexis_eligible_opinions.csv` contains one row per eligible operative opinion and provides the input for the case coverage calculation. `lexis_district_segment.csv` cross-references the report views for the eight district court entries.

`citation_sample_checks.csv` reports pair counts by sampled citing opinion. `c1_outcome_source_checks.csv` records excerpt and controlling-window checks by issue.
