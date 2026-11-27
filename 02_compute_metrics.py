"""Build graph files and compute centrality, hierarchy, and PageRank sensitivity."""

from itertools import combinations

import networkx as nx
from scipy.stats import kendalltau, spearmanr

from _data import analysis_output, load_corpus, write_csv

ALPHAS = (0.75, 0.85, 0.90, 0.95)


def pagerank(graph, alpha=0.85):
    return nx.pagerank(graph, alpha=alpha, tol=1e-12, max_iter=1000)


def order(scores):
    return sorted(scores, key=lambda n: (-round(scores[n], 10), n))


def rank(scores, node):
    return 1 + sum(round(value, 10) > round(scores[node], 10) for value in scores.values())


def correlation(a, b, method=kendalltau):
    if len(a) < 2 or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    return float(method(a, b).statistic)


def rank_agreement(reference, scores, method=kendalltau):
    common = sorted(reference.keys() & scores.keys())
    return correlation([round(reference[n], 10) for n in common],
                       [round(scores[n], 10) for n in common], method)


def levels(graph):
    depth = {}
    for n in reversed(list(nx.topological_sort(graph))):
        depth[n] = 1 + max((depth[t] for t in graph.successors(n)), default=-1)
    return depth


def analyze_graphs(graphs, output):
    metrics, summary, alpha_rows, alpha_agreement, hierarchy = [], [], [], [], []
    reference = pagerank(graphs["baseline"])
    for label, graph in graphs.items():
        scores = pagerank(graph)
        depth = levels(graph)
        between = nx.betweenness_centrality(graph)
        filename = "s230_graph.graphml" if label == "baseline" else f"{label}.graphml"
        nx.write_graphml_xml(graph, output / filename)
        summary.append(dict(graph=label, opinions=len(graph), edges=graph.size(),
                            isolates=nx.number_of_isolates(graph),
                            weak_components=nx.number_weakly_connected_components(graph),
                            kendall_tau_b=rank_agreement(reference, scores),
                            top_five_ids=" ".join(order(scores)[:5]),
                            top_five_names=" | ".join(graph.nodes[n]["case_name"] for n in order(scores)[:5])))
        for n in order(scores):
            metrics.append(dict(graph=label, opinion_id=n, **graph.nodes[n],
                                in_degree=graph.in_degree(n), out_degree=graph.out_degree(n),
                                pagerank=scores[n], rank=rank(scores, n),
                                directed_betweenness=between[n], dag_depth=depth[n]))
        for cohort, nodes in [("all", sorted(graph)),
                              ("inbound", sorted(n for n in graph if graph.in_degree(n)))]:
            hierarchy.append(dict(graph=label, cohort=cohort, opinions=len(nodes),
                                  spearman_rho=correlation([depth[n] for n in nodes],
                                                          [round(scores[n], 10) for n in nodes], spearmanr)))
        by_alpha = {alpha: pagerank(graph, alpha) for alpha in ALPHAS}
        for alpha, values in by_alpha.items():
            alpha_rows.extend(dict(graph=label, alpha=alpha, opinion_id=n, pagerank=values[n],
                                   rank=rank(values, n)) for n in order(values))
        for a, b in combinations(ALPHAS, 2):
            alpha_agreement.append(dict(graph=label, alpha_a=a, alpha_b=b,
                                        kendall_tau_b=rank_agreement(by_alpha[a], by_alpha[b]),
                                        spearman_rho=rank_agreement(by_alpha[a], by_alpha[b], spearmanr)))
    write_csv(output / "graph_summary.csv", summary)
    write_csv(output / "s230_metrics.csv", metrics)
    write_csv(output / "dag_depth_association.csv", hierarchy)
    write_csv(output / "pagerank_damping.csv", alpha_rows)
    write_csv(output / "pagerank_damping_agreement.csv", alpha_agreement)
    return summary, reference


if __name__ == "__main__":
    output = analysis_output(__doc__)
    _, _, _, edges, graphs, _ = load_corpus()
    write_csv(output / "edge_evidence.csv", edges)
    analyze_graphs(graphs, output)
