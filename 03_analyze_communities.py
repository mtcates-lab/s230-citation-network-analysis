"""Leiden stability, consensus assignment, and graph perturbation checks."""

from collections import Counter
import re
from functools import lru_cache
from itertools import combinations_with_replacement

import igraph as ig
import leidenalg
import networkx as nx
import numpy as np
from sklearn.metrics import adjusted_mutual_info_score, mutual_info_score, normalized_mutual_info_score

from _data import OUTCOMES, analysis_output, load_corpus, write_csv
from importlib import import_module

metrics = import_module("02_compute_metrics")
pagerank = metrics.pagerank
levels = metrics.levels

RESOLUTIONS = (0.75, 1.0, 1.25)
CONSENSUS_THRESHOLD = 0.80
SEEDS = range(100)


def leiden(graph, resolution=1.0, seed=42, directed=False):
    nodes = sorted(graph)
    index = {n: i for i, n in enumerate(nodes)}
    edges = [(index[s], index[t]) for s, t in graph.edges]
    if not directed:
        edges = [(min(s, t), max(s, t)) for s, t in edges]
    if not edges:
        return tuple(range(len(nodes))), 0.0
    projection = ig.Graph(n=len(nodes), edges=sorted(edges), directed=directed)
    partition = leidenalg.find_partition(projection, leidenalg.RBConfigurationVertexPartition,
                                        resolution_parameter=resolution, seed=seed, n_iterations=-1)
    canonical = {}
    labels = tuple(canonical.setdefault(k, len(canonical)) for k in partition.membership)
    return labels, float(partition.modularity)


@lru_cache(maxsize=10000)
def partition_nmi(a, b):
    return float(normalized_mutual_info_score(a, b))


def pairwise_nmi(partitions):
    frequencies = Counter(partitions)
    pairs = []
    for a, b in combinations_with_replacement(sorted(frequencies), 2):
        count = frequencies[a] * frequencies[b] if a != b else frequencies[a] * (frequencies[a] - 1) // 2
        if count:
            pairs.append((partition_nmi(a, b), count))
    return sum(score * count for score, count in pairs) / sum(count for _, count in pairs), min(s for s, _ in pairs)


def consensus(nodes, partitions):
    assignments = np.asarray(partitions)
    coassignment = (assignments[:, :, None] == assignments[:, None, :]).mean(axis=0)
    # Complete-link merge requires every cross-group pair to clear the threshold.
    groups = [(i,) for i in range(len(nodes))]
    while len(groups) > 1:
        score, a, b = max((float(coassignment[np.ix_(ga, gb)].min()), -i, -j)
                         for i, ga in enumerate(groups) for j, gb in enumerate(groups) if i < j)
        if score < CONSENSUS_THRESHOLD:
            break
        groups[-a] = tuple(sorted(groups[-a] + groups[-b]))
        del groups[-b]
    assignment = {nodes[i]: k for k, group in enumerate(groups, 1) for i in group}
    return assignment, coassignment


def outcome_association(graph_label, assignments, opinions):
    rows = []
    rng = np.random.default_rng(23014)
    for label, assignment in assignments.items():
        for scope, field in (("all", "derived_claim_outcome"), ("c1", "derived_c1_outcome")):
            nodes = sorted(n for n in assignment if opinions[n][field] in OUTCOMES)
            groups = [assignment[n] for n in nodes]
            outcomes = [opinions[n][field] for n in nodes]
            score = mutual_info_score(groups, outcomes)
            null = [mutual_info_score(groups, rng.permutation(outcomes)) for _ in range(999)]
            rows.append(dict(graph=graph_label, partition=label, scope=scope, opinions=len(nodes),
                             all_barred=outcomes.count("All barred"), none_barred=outcomes.count("None barred"),
                             mixed=outcomes.count("Mixed"), communities=len(set(groups)),
                             mutual_information_nats=float(score),
                             normalized_mi=float(normalized_mutual_info_score(groups, outcomes)),
                             adjusted_mi=float(adjusted_mutual_info_score(groups, outcomes)),
                             permutation_p=(1 + sum(x >= score - 1e-12 for x in null)) / 1000))
    return rows


def analyze_partitions(graphs, opinions, output):
    stability, runs, assignments, paired, associations, tables = [], [], [], [], [], []
    references = {}
    for label in ("baseline", "section_230", "c1_baseline", "c1_section_230", "full_reporter"):
        graph = graphs[label]
        nodes = sorted(graph)
        best, _ = leiden(graph)
        references[label] = best
        for res in RESOLUTIONS if label != "full_reporter" else (1.0,):
            partitions = [leiden(graph, res, seed) for seed in SEEDS]
            all_assignments = [p for p, _ in partitions]
            mean, minimum = pairwise_nmi(all_assignments)
            sizes = [len(set(p)) for p in all_assignments]
            stability.append(dict(graph=label, resolution=res, runs=len(partitions),
                                  fewest_communities=min(sizes), most_communities=max(sizes),
                                  mean_pairwise_nmi=mean, min_pairwise_nmi=minimum))
            for seed, (p, q) in enumerate(partitions):
                runs.append(dict(graph=label, resolution=res, seed=seed, communities=len(set(p)),
                                 modularity_at_gamma_1=q, nmi_vs_seed_42_gamma_1=partition_nmi(best, p),
                                 membership=" ".join(map(str, p))))
            if res != 1.0:
                continue
            agree, matrix = consensus(nodes, all_assignments)
            fixed = {n: k + 1 for n, k in zip(nodes, best)}
            assignments.extend(dict(graph=label, opinion_id=n, reference_group=fixed[n],
                                    consensus_group=agree[n]) for n in nodes)
            paired.extend(dict(graph=label, opinion_a=n, opinion_b=m, coassignment=float(matrix[i, j]))
                          for i, n in enumerate(nodes) for j, m in enumerate(nodes) if j > i)
            partitions_for_outcomes = {"seed_42": fixed, "consensus": agree}
            associations.extend(outcome_association(label, partitions_for_outcomes, opinions))
            for method, assignment in partitions_for_outcomes.items():
                for scope, field in (("all", "derived_claim_outcome"), ("c1", "derived_c1_outcome")):
                    counts = Counter((group, opinions[n][field]) for n, group in assignment.items())
                    tables.extend(dict(graph=label, partition=method, scope=scope, community=group,
                                       outcome=category, opinions=counts[group, category])
                                  for group in sorted(set(assignment.values()))
                                  for category in (*OUTCOMES, "No resolved claim outcome"))
    for file, data in (("leiden_stability", stability), ("leiden_runs", runs),
                       ("community_membership", assignments), ("coassignment", paired),
                       ("community_outcome_mi", associations), ("community_outcome_counts", tables)):
        write_csv(output / f"{file}.csv", data)
    baseline = graphs["baseline"].copy()
    scores, depth = pagerank(baseline), levels(baseline)
    for row in assignments:
        if row["graph"] != "baseline":
            continue
        n = row["opinion_id"]
        baseline.nodes[n].update(label=baseline.nodes[n]["case_name"], community=row["reference_group"],
                                 consensus_group=row["consensus_group"], pagerank=scores[n],
                                 in_degree=baseline.in_degree(n), out_degree=baseline.out_degree(n), dag_depth=depth[n])
    path = output / "s230_graph_attributed.gexf"
    nx.write_gexf(baseline, path)
    path.write_text(re.sub(r' lastmodifieddate="[^"]+"', "", path.read_text(encoding="utf-8"), count=1),
                    encoding="utf-8")
    return stability, references


if __name__ == "__main__":
    output = analysis_output(__doc__)
    opinions, _, _, _, graphs, _ = load_corpus()
    analyze_partitions(graphs, opinions, output)
