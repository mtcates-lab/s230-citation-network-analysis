# Replication guide

## 1. Reproduce the analysis

Use Python 3.12. Install the pinned packages from `requirements.txt`, then run:

```bash
python run_analysis.py --output reproduced
python verify_results.py --output reproduced
```

Run `python run_analysis.py` to write results into `data/`. Each numbered analysis script also accepts `--output` for running an individual step elsewhere. The analysis takes the bundled tables as inputs. It runs offline once dependencies are installed. The scripts use paths relative to the repository and can be launched from another working directory. Use a fresh output directory when comparing runs. The verifier checks the input hashes, graph exports, citation and issue totals, and selected results. An intentionally revised dataset requires new expectations.

## 2. Read the outputs

| Output | Calculation |
| --- | --- |
| `summary.json` | Dataset identifier, input hashes, dependency versions, graph totals, outcomes, circuit and Leiden summaries, export crosswalk counts, and citation-function counts |
| `edge_evidence.csv` | Passage-derived flags and supporting IDs for each candidate pair, including the pair omitted from the baseline |
| `graph_summary.csv`, `s230_metrics.csv` | Directed graph sizes, components, ranking, in-degree, out-degree, normalized directed betweenness, and DAG depth |
| `*.graphml`, `*.gexf` | GraphML covers all ten variants. The baseline GEXF also includes PageRank, depth, and community labels |
| `pagerank_damping*.csv`, `dag_depth_association.csv` | Score and rank sensitivity, and Spearman association in the whole graph and among nodes with at least one inbound edge |
| `temporal_snapshots.csv`, `year_end_pagerank.csv`, `five_year_opportunity.csv` | Annual network and rank history, and citation counts within each eligible opinion’s first five years |
| `circuit_flows.csv`, `circuit_divergence*.csv` | Court-to-court edge counts, pooled and fixed-target era comparisons, annual pair estimates and denominator checks |
| `leiden_runs.csv`, `leiden_stability.csv` | Seed-by-seed results and pairwise partition agreement |
| `community_membership.csv`, `coassignment.csv`, `community_outcome_mi.csv`, `community_outcome_counts.csv` | Reference and consensus assignments, pair co-membership, outcome tables, and descriptive association |
| `node_removal.csv`, `edge_removal*.csv` | Targeted and random perturbation trials |
| `poincare_embedding.csv`, `poincare_fit.csv` | Exploratory coordinates and fit summaries |
| `outcomes.csv`, `publisher_outcome_comparison.csv`, `fosta_holdings.csv` | Period counts and denominators, case-level primary and broader outcome assignments, and the FOSTA comparison |
| `pagerank_chronology.csv`, `leiden_chronology.csv` | Observed PageRank and baseline modularity alongside 500 simulations conditioned on opinion date and outgoing citation count |
| `leiden_partition_comparison.csv`, `leiden_partition_membership.csv` | Group counts, agreement, and membership for the reference, consensus, and directed partitions |
| `baseline_circuit_period_comparison.csv` | Circuit-pair contributions, fixed targets, divergence, and threshold eligibility for both eras |
| `precedent_citation_contributions.csv` | Baseline incoming edge contributions for Ben Ezra and Roommates.com, with passage IDs and citation functions |
| `candidate_crosswalk.csv`, `citation_functions.csv`, `citations_by_target_and_function.csv` | Candidate date, match status, and recorded screening decisions; coded function frequencies; and counts by cited opinion |

## 3. Parameters

**Centrality and hierarchy.** PageRank uses the directed unweighted graph, uniform teleportation and dangling redistribution, α = 0.85, tolerance 10⁻¹², and a maximum of 1,000 iterations. The damping sweep uses 0.75, 0.85, 0.90, and 0.95. Ranking rounds scores to ten decimal places for ties. Fixed-size top lists break ties by opinion ID. DAG depth is the longest directed path from the node to a node with zero outgoing edges. A terminal node has depth zero. Directed betweenness uses shortest citation paths.

**Time.** Each December 31 snapshot includes the opinions already decided and audited edges between them. The density denominator counts ordered pairs for which the source decision date follows the target date. These are retrospective snapshots of the audited dataset. Historical editions and indexing dates are outside this reconstruction. Five-year opportunity counts later opinions issued within the same five-year horizon, with a separate within-circuit denominator. The follow-up window must end by December 31, 2025.

**Circuit divergence.** For each citing circuit, normalize its outgoing edge counts over the same set of target opinions. Square SciPy’s Jensen–Shannon distance with logarithm base 2 to obtain divergence in bits on [0, 1]. The minimum screen requires two contributing opinions and five eligible edges per circuit. The strict screen requires three and ten. The pre/post comparison holds the targets fixed to the pre-enactment opinions. Annual rows group citing opinions within one calendar year, using available targets through that year end. Sparse and undefined rows stay visible. Do not compare averages across years as changes in a fixed set of circuit pairs.

**Communities.** Leiden uses the unweighted undirected projection, the RB configuration objective, resolution values 0.75, 1.0, and 1.25, seeds 0–99, and iterations until convergence. The reference is seed 42 at resolution 1.0. The reported modularity column evaluates each label set at resolution 1.0. Membership strings use zero-based labels in sorted opinion-ID order. The stability table reports mean and minimum normalized mutual information over all unordered run pairs. Consensus uses complete-link merging of co-assignment frequencies at 0.80, with deterministic ties. The outcome analysis keeps mixed results and excludes unresolved opinions. It reports raw mutual information in nats, normalized and adjusted MI, and a descriptive permutation comparison with 999 label shuffles per configuration. The permutation test conditions on the recorded outcomes and ignores differences in period, posture, and court.

**Perturbations.** Node removal follows a fixed initial PageRank or in-degree order, or 100 random orders (seed 23021). The component share uses the original graph size. Edge removal samples 5%, 10%, 20%, and 30% of edges without replacement, with 100 seeds per level and nodes held fixed. Report tie-aware Kendall τ-b, top-five overlap and partition NMI. These are graph sensitivity checks under the specified perturbations.

**Hyperbolic embedding.** The two full graphs are projected to undirected edges. The two-dimensional Poincaré model contrasts each oriented positive neighbor with ten sampled nonneighbors. It uses a softmax over negative hyperbolic distances and a Riemannian gradient update for 300 epochs at learning rate 0.05, with seeds 42–44. Isolates have no fit. The output records both Euclidean disk radius and hyperbolic distance from the origin, measured as twice the inverse hyperbolic tangent of the radius. The radial correlation is exploratory and depends on the fitted origin and objective.

**Outcomes.** All-barred, none-barred, and mixed classifications follow the issue codes. Period tables report counts and the resolved denominator, including five-year bins from 2000, an initial partial bin, and a separate 2025 row. The full pre/post comparison and equal-length pre-enactment window use the same post-enactment endpoint. The carveout sensitivity excludes the four opinions with a direct-carveout row, even if they also contain a separate issue.

**Publication checks.** With seed 230, sample earlier target opinions uniformly without replacement for each citing opinion. Keep its observed outgoing citation count. Record the observed baseline PageRank and simulated first-place count, median, and central 95% range. Run undirected Leiden at resolution 1.0 with seed 42 on each simulated graph to compare modularity. On the observed graph, use the same resolution and seed with edges directed from citing to cited opinion to compare membership with the undirected reference and consensus partitions. Incoming contributions to PageRank are the source’s PageRank multiplied by 0.85 and divided by its outgoing edge count. The common teleportation and dangling-node terms enter each target score separately.

## 4. Retrieve candidates and check recall

Print the saved search parameters with `python 01_collect_data.py --show-query`. To collect a new candidate export, set `COURTLISTENER_TOKEN` in your environment and run `python 01_collect_data.py`. Keep the resulting JSON with its query parameters and the corresponding CSV together. The live query produces a new search snapshot. The supplied TSV is the preserved result for this study. `validation/candidate_screening.csv` holds the screening decisions. Each run joins those fields to the generated crosswalk by cluster ID and rejects a mismatched candidate set. The raw export stays unchanged. A live authenticated call was outside the reference run.

For case recall, supply a CSV with one unique operative `reporter_citation` per independently verified eligible opinion. For edge recall, supply one row per independently enumerated controlling citation pair, with `citing_opinion_id,cited_opinion_id`. Supply a second CSV with one `citing_opinion_id` per independently and fully checked citing opinion, including opinions with zero citations to other included opinions. Record how the independent opinions were selected and how short forms and separate writings were handled.

```bash
python 07_estimate_recall.py case validation/lexis_eligible_opinions.csv --output case_recall.json
python 07_estimate_recall.py edge edge_reference.csv --sample audited_opinions.csv --output edge_recall.json
```

These commands measure exact recovery in the supplied reference set. The Shepard’s case comparison recovers 56 of 56 eligible opinions identified in the captured appellate records. Edge recall remains unmeasured. See the [coverage audit](validation/lexis_coverage.md) for the report scope and [coding checks](validation/coding_checks.md) for the additional citation and issue checks.

The included `data/recall_sample.json` specifies a simple random sample of 20 citing opinions, without replacement, using seed 23019. An estimate requires the independently enumerated reference set.

## 5. Optional citation-parser replay

The repository includes `eyecite_results.json` and `eyecite_edges.json` in `data/`. The first preserves parser tokens and source lines for each opinion. The second aggregates leads to earlier included opinions and compares them with the audited baseline. Candidates can include citations in background material and separate opinions. The overlap is a parser diagnostic. Graph construction uses the audited passage flags.

To regenerate the two parser exports, use the bundled working compilation and the six court copies in `sources/recovered/`. The opinion CSV supplies the source ranges. The output records source checksums.

```bash
python -m pip install -r requirements-eyecite.txt
python 08_extract_eyecite.py sources/controlling/combined_opinions.txt
python verify_results.py
```

## 6. Source and screening tables

Analysis inputs and generated results are stored under `data/`. Opinion texts are stored under `sources/`. Screening decisions and validation tables are stored under `validation/`. The scripts read the screening ledger at `validation/candidate_screening.csv` and regenerate `data/candidate_crosswalk.csv`.

`validation/candidate_screening.csv` holds the candidate decisions and evidence. The generated crosswalk joins these fields by cluster ID. All 217 records have final decisions. Dart and Children’s Health Defense are integrated in this 56-opinion dataset. Corrected dates and reporter citations appear beside the preserved export metadata. The provenance table retains Paxton and identifies its verified source; its original discovery route is not recorded.

The opinion-boundary, passage-part, and edge-boundary tables document the controlling text and supporting passages. Source lines count newline-delimited lines from one in the named file. Where one line contains both the end of the majority and the start of a separate writing, use the delimiter in the boundary table.

The input contains 825 passage records, including 823 coded passages and two excluded source artifacts. The baseline and statutory graphs have 317 and 310 edges. The full-reporter sensitivity graph has 306 edges. Adding or removing eligible opinions requires new issue and citation coding and a new analysis run.
