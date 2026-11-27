"""Reproduce the Section 230 network results from the coded inputs."""

import argparse
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from importlib import import_module
import _data as inputs

metrics = import_module("02_compute_metrics")
communities = import_module("03_analyze_communities")
historical = import_module("04_analyze_circuits_and_time")
outcome = import_module("05_analyze_outcomes")
robustness = import_module("06_test_robustness")
import publication_checks as publication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=inputs.ROOT / "data")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    opinions, issues, passages, edges, graphs, fosta = inputs.load_corpus()
    inputs.write_csv(out / "edge_evidence.csv", edges)
    tables, baseline_scores = metrics.analyze_graphs(graphs, out)
    historical.analyze_time(graphs, opinions, out, communities.leiden)
    divergence = historical.analyze_circuits(graphs, opinions, out)
    outcomes = outcome.analyze_outcomes(opinions, issues, fosta, out)
    stability, references = communities.analyze_partitions(graphs, opinions, out)
    robustness.analyze_perturbations(graphs, references, out)
    robustness.analyze_embeddings(graphs, out)
    status = Counter(r["coding_status"] for r in passages.values())
    functions = Counter(r["citation_function"] for r in passages.values()
                        if r["coding_status"] == "Coded")
    inputs.write_csv(out / "citation_functions.csv",
                     [dict(citation_function=k, passages=v) for k, v in sorted(functions.items())])
    target_functions = {}
    for r in passages.values():
        if r["cited_opinion_id"] and r["citing_use"] == inputs.COURT_USE:
            key = (r["cited_opinion_id"], r["citation_function"])
            target_functions.setdefault(key, []).append(r)
    inputs.write_csv(out / "citations_by_target_and_function.csv", [
        dict(cited_opinion_id=n, citation_function=f, passages=len(rows),
             unique_citing_opinions=len({r["citing_opinion_id"] for r in rows}),
             cross_circuit_passages=sum(opinions[r["citing_opinion_id"]]["circuit"] != opinions[n]["circuit"]
                                        for r in rows))
        for (n, f), rows in sorted(target_functions.items())
    ])
    publication.run_checks(opinions, passages, edges, graphs["baseline"], out)
    summary = dict(dataset="s230-appellate-56", opinions=len(opinions), issues=len(issues),
                   passage_records=len(passages), passage_coding_status=status, in_corpus_candidate_pairs=len(edges),
                   graph_summary=tables, highest_baseline_pagerank=max(baseline_scores.values()),
                   circuit_divergence=divergence, outcome_counts=outcomes, leiden_stability=stability,
                   candidate_export=inputs.audit_search(opinions, out),
                   versions={k: version(k) for k in ("networkx", "scipy", "numpy", "igraph",
                                                     "leidenalg", "scikit-learn")},
                   input_sha256=inputs.input_hashes())
    inputs.write_json(out / "summary.json", summary)
    for row in tables:
        print(f"{row['graph']}: {row['opinions']} opinions, {row['edges']} edges")


if __name__ == "__main__":
    main()
