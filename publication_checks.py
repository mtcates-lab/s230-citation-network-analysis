"""Reproduce citation-opportunity, partition, and circuit-period comparisons."""

from collections import Counter
from importlib import import_module

import networkx as nx
import numpy as np

from _data import read_csv, write_csv

metrics = import_module("02_compute_metrics")
communities = import_module("03_analyze_communities")
TRIALS = 500
SEED = 230
ALPHA = 0.85


def compare_chronology(graph, opinions, output):
    nodes = sorted(graph)
    earlier = {
        source: [target for target in nodes
                 if opinions[target]["decision_date"] < opinions[source]["decision_date"]]
        for source in nodes
    }
    rng = np.random.default_rng(SEED)
    scores = metrics.pagerank(graph, alpha=ALPHA)
    simulated = {node: [] for node in nodes}
    first = Counter()
    modularities = []
    for _ in range(TRIALS):
        randomized = nx.DiGraph()
        randomized.add_nodes_from(nodes)
        for source in nodes:
            targets = rng.choice(earlier[source], size=graph.out_degree(source), replace=False)
            randomized.add_edges_from((source, target) for target in targets)
        trial_scores = metrics.pagerank(randomized, alpha=ALPHA)
        for node in nodes:
            simulated[node].append(trial_scores[node])
            first[node] += metrics.rank(trial_scores, node) == 1
        modularities.append(communities.leiden(randomized)[1])

    write_csv(output / "pagerank_chronology.csv", [
        dict(opinion_id=node, case_name=opinions[node]["case_name"], trials=TRIALS, seed=SEED,
             observed_pagerank=scores[node], observed_rank=metrics.rank(scores, node),
             incoming_links=graph.in_degree(node), null_first_place_trials=first[node],
             null_lower_025=float(np.quantile(simulated[node], .025)),
             null_median=float(np.median(simulated[node])),
             null_upper_975=float(np.quantile(simulated[node], .975)))
        for node in metrics.order(scores)
    ])
    write_csv(output / "leiden_chronology.csv", [
        dict(graph="baseline", trials=TRIALS, seed=SEED, resolution=1.0,
             observed_modularity=communities.leiden(graph)[1],
             null_lower_025=float(np.quantile(modularities, .025)),
             null_median=float(np.median(modularities)),
             null_upper_975=float(np.quantile(modularities, .975)))
    ])


def compare_partitions(graph, output):
    nodes = sorted(graph)
    reference, _ = communities.leiden(graph)
    directed, _ = communities.leiden(graph, directed=True)
    membership = {row["opinion_id"]: int(row["consensus_group"])
                  for row in read_csv(output / "community_membership.csv") if row["graph"] == "baseline"}
    consensus = tuple(membership[node] for node in nodes)
    labels = {"reference": reference, "consensus": consensus, "directed": directed}
    write_csv(output / "leiden_partition_comparison.csv", [
        dict(partition=name, groups=len(set(values)),
             nmi_with_reference=communities.partition_nmi(reference, values),
             nmi_with_consensus=communities.partition_nmi(consensus, values),
             nmi_with_directed=communities.partition_nmi(directed, values))
        for name, values in labels.items()
    ])
    write_csv(output / "leiden_partition_membership.csv", [
        dict(opinion_id=node, reference_group=reference[i] + 1,
             consensus_group=consensus[i], directed_group=directed[i] + 1)
        for i, node in enumerate(nodes)
    ])


def compare_circuit_periods(output):
    rows = read_csv(output / "circuit_divergence.csv")
    eras = ("before_fixed_targets", "since_fixed_targets")
    groups = [{(r["court_a"], r["court_b"]): r for r in rows
               if r["graph"] == "baseline" and r["period"] == era} for era in eras]
    fields = ("opinions_a", "opinions_b", "citing_opinions_a", "citing_opinions_b",
              "edges_a", "edges_b", "targets", "jsd_bits", "minimum", "strict")
    comparison = []
    for court_a, court_b in sorted(groups[0].keys() | groups[1].keys()):
        before, since = (group.get((court_a, court_b), {}) for group in groups)
        comparison.append(dict(court_a=court_a, court_b=court_b,
                               minimum_both=int(before.get("minimum") == since.get("minimum") == "1"),
                               strict_both=int(before.get("strict") == since.get("strict") == "1"),
                               **{f"{era}_{field}": row.get(field, "")
                                  for era, row in (("before", before), ("since", since))
                                  for field in fields}))
    write_csv(output / "baseline_circuit_period_comparison.csv", comparison)


def citation_contributions(graph, opinions, passages, evidence, output):
    scores = metrics.pagerank(graph, alpha=ALPHA)
    focus = {"206 F.3d 980", "521 F.3d 1157"}
    rows = []
    for edge in evidence:
        source, target = edge["citing_opinion_id"], edge["cited_opinion_id"]
        if not edge["baseline"] or opinions[target]["reporter_citation"] not in focus:
            continue
        supporting = edge["baseline_passage_ids"].split()
        rows.append(dict(target_id=target, target_case=opinions[target]["case_name"],
                         citing_id=source, citing_case=opinions[source]["case_name"],
                         citing_pagerank=scores[source], citing_outdegree=graph.out_degree(source),
                         edge_contribution=ALPHA * scores[source] / graph.out_degree(source),
                         passage_ids=" ".join(supporting),
                         citation_functions=" | ".join(sorted({passages[pid]["citation_function"]
                                                              for pid in supporting}))))
    rows.sort(key=lambda row: (row["target_id"], -row["edge_contribution"], row["citing_id"]))
    write_csv(output / "precedent_citation_contributions.csv", rows)


def run_checks(opinions, passages, evidence, baseline, output):
    compare_chronology(baseline, opinions, output)
    compare_partitions(baseline, output)
    compare_circuit_periods(output)
    citation_contributions(baseline, opinions, passages, evidence, output)

