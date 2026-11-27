# § 230 Citation Network

A computational analysis of the federal appellate citation network for 47 U.S.C. § 230, 1997–2025.

## Overview

This repository contains the data, Python code, and documentation for a citation network analysis of 56 published federal appellate opinions. The study uses two directed graphs. The baseline records citations the court uses in its own discussion. The § 230 graph keeps links with at least one passage used in statutory reasoning. A 43-opinion comparison limits the case set to independently decided § 230(c)(1) publisher or third-party-source questions.

The current dataset contains 75 coded issues and 823 coded citation passages. The search scope includes published opinions from the courts of appeals and the Supreme Court. This release includes 56 court-of-appeals opinions and no Supreme Court opinion from the screened candidate set. The 56 included opinions match all 56 eligible opinions identified in the captured Shepard’s appellate records. See the [coverage audit](validation/lexis_coverage.md) for the reference set and its limits.

## Key findings

- *Zeran v. America Online* leads the baseline graph (PageRank 0.1909, 31 incoming links). It also ranks first in all 500 simulations that redistribute citations among earlier opinions while holding each opinion’s outgoing count fixed. Its observed score exceeds the simulated 97.5th percentile of 0.1873.
- *Ben Ezra* ranks second in the baseline with 10 incoming links. *Roommates.com* ranks sixth with 26. The [citation contributions](data/precedent_citation_contributions.csv) identify the citing opinions and supporting passages behind those ranks.
- The 56-opinion baseline has 317 links. The § 230 reasoning graph has 310. The corresponding 43-opinion graphs have 269 and 266 links.
- Baseline Leiden runs at resolution 1.0 return four to six communities across 100 seeds (mean pairwise NMI = 0.825). The directed check produces five groups, compared with four in the undirected reference run (NMI = 0.808).
- Mean pairwise Jensen–Shannon divergence in the pooled baseline is 0.462 bits across 55 eligible circuit pairs (range 0.236–0.655). Each circuit in a pair contributes at least two citing opinions and five edges. Only the Second and Ninth Circuits qualify as a pair in both eras under that threshold (approximately 0.429 bits in each).
- Before the April 11, 2018 FOSTA-SESTA cutoff, 17 of 23 opinions with a resolved § 230(c)(1) outcome barred every coded theory. From the cutoff through 2025, 8 of 19 did so. The broader comparison adds publisher-based preemption rulings and gives 17 of 24 and 8 of 21. The separate FOSTA table tracks the statutory questions each opinion decided.

The full-reporter sensitivity graph has 306 links. All 217 candidate records have a final decision: 55 Include, 122 Exclude, and 40 Duplicate. The 55 included CourtListener records account for 55 of the 56 included opinions. The remaining opinion, *Free Speech Coalition v. Paxton*, is documented in the [discovery provenance table](validation/discovery_provenance.csv). Its original discovery route is not recorded.

## Repository structure

The numbered Python files are in the root. Analysis inputs and outputs are in `data/`. Opinion texts are in `sources/`. Screening records and audit tables are in `validation/`.

| Script | Purpose |
| --- | --- |
| [01_collect_data.py](01_collect_data.py) | Re-run the CourtListener search |
| [02_compute_metrics.py](02_compute_metrics.py) | Build the graphs and compute PageRank, betweenness, and DAG depth |
| [03_analyze_communities.py](03_analyze_communities.py) | Run Leiden, form consensus groups, and compare communities with coded outcomes |
| [04_analyze_circuits_and_time.py](04_analyze_circuits_and_time.py) | Compare circuits and build annual snapshots |
| [05_analyze_outcomes.py](05_analyze_outcomes.py) | Summarize issue outcomes and the FOSTA comparison |
| [06_test_robustness.py](06_test_robustness.py) | Test node and edge removal and fit exploratory embeddings |
| [07_estimate_recall.py](07_estimate_recall.py) | Estimate recall from an independent reference set |
| [08_extract_eyecite.py](08_extract_eyecite.py) | Replay citation parsing on the source text |

Open [included_opinions.csv](data/included_opinions.csv) for the 56 included opinions, [s230_metrics.csv](data/s230_metrics.csv) for opinion-level results, and [graph_summary.csv](data/graph_summary.csv) for all graph variants. The baseline is available in [GraphML](data/s230_graph.graphml) and as an [attributed GEXF](data/s230_graph_attributed.gexf) for Gephi.

## Reproducing the analysis

Python 3.12 was used for the reference run. `run_analysis.py` runs steps 02–06 against the bundled data, then runs the publication checks. Data collection, recall estimation, and parser replay can be run separately.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_analysis.py --output reproduced
python verify_results.py --output reproduced
```

The MIT license covers the software and documentation. The coded CSVs identify the study data, and the court opinions are attributed source materials.

See [replication_guide.md](replication_guide.md) for output descriptions and [research_design.md](research_design.md) for the graph and screening rules. [Results](results.md) connect the network measures to the controlling passages.

## Citing this dataset

Cates, M. (2026). *Section 230 citation network analysis* [Data set and analysis code]. GitHub. https://github.com/mtcates-lab/s230-citation-network-analysis
