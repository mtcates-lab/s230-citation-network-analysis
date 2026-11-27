"""Run removal simulations and exploratory Poincaré embeddings."""

import networkx as nx
import numpy as np
from scipy.special import softmax
from scipy.stats import spearmanr

from importlib import import_module

from _data import analysis_output, load_corpus, write_csv
metrics = import_module("02_compute_metrics")
communities = import_module("03_analyze_communities")
pagerank = metrics.pagerank
correlation = metrics.correlation
order = metrics.order
rank_agreement = metrics.rank_agreement
leiden = communities.leiden
partition_nmi = communities.partition_nmi

SEEDS = (42, 43, 44)
EPOCHS = 300
NEGATIVES = 10
LEARNING_RATE = 0.05


def distances_and_gradients(u, v):
    alpha = 1 - np.sum(u * u, axis=-1, keepdims=True)
    beta = 1 - np.sum(v * v, axis=-1, keepdims=True)
    delta = u - v
    distance_sq = np.sum(delta * delta, axis=-1, keepdims=True)
    gamma = np.maximum(1 + 2 * distance_sq / (alpha * beta), 1 + 1e-12)
    factor = 4 / (alpha * beta * np.sqrt(gamma * gamma - 1))
    grad_u = factor * (delta + u * distance_sq / alpha)
    grad_v = factor * (-delta + v * distance_sq / beta)
    return np.arccosh(gamma)[..., 0], grad_u, grad_v


def embed(graph, seed):
    projection = graph.to_undirected()
    nodes = sorted(n for n in projection if projection.degree(n))
    index = {n: i for i, n in enumerate(nodes)}
    sources, positives = [], []
    for s in nodes:
        for t in sorted(projection[s]):
            sources.append(index[s])
            positives.append(index[t])
    sources, positives = np.asarray(sources), np.asarray(positives)
    negative_pool = [sorted(set(index.values()) - {i} - {index[t] for t in projection[n]})
                     for i, n in enumerate(nodes)]
    valid = np.array([bool(negative_pool[i]) for i in sources])
    sources, positives = sources[valid], positives[valid]
    rng = np.random.default_rng(seed)
    x = rng.uniform(-0.001, 0.001, (len(nodes), 2))
    losses = []
    for epoch in range(EPOCHS):
        negatives = np.array([rng.choice(negative_pool[i], size=NEGATIVES) for i in sources])
        contrasts = np.column_stack((positives, negatives))
        u, v = x[sources, None, :], x[contrasts]
        distance, gu, gv = distances_and_gradients(u, v)
        prob = softmax(-distance, axis=1)
        losses.append(float(-np.log(prob[:, 0]).mean()))
        slope = -prob
        slope[:, 0] += 1
        grad = np.zeros_like(x)
        np.add.at(grad, sources, np.sum(slope[..., None] * gu, axis=1))
        np.add.at(grad, contrasts, slope[..., None] * gv)
        conformal = ((1 - np.sum(x * x, axis=1, keepdims=True)) ** 2) / 4
        x -= LEARNING_RATE * conformal * grad / max(1.0, len(sources) / len(nodes))
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        x *= np.minimum(1, 0.99999 / np.maximum(norm, 1e-12))
    return nodes, x, losses


def analyze_embeddings(graphs, output):
    rows, fit = [], []
    for label in ("baseline", "section_230"):
        graph = graphs[label]
        scores = pagerank(graph)
        for seed in SEEDS:
            nodes, x, losses = embed(graph, seed)
            radii = np.linalg.norm(x, axis=1)
            distance = 2 * np.arctanh(radii)
            rows.extend(dict(graph=label, seed=seed, opinion_id=n, x=float(point[0]), y=float(point[1]),
                             radius=float(r), distance_from_origin=float(d), pagerank=scores[n])
                        for n, point, r, d in zip(nodes, x, radii, distance))
            fit.append(dict(graph=label, seed=seed, embedded=len(nodes), isolates_excluded=nx.number_of_isolates(graph),
                            epochs=EPOCHS, negatives=NEGATIVES, learning_rate=LEARNING_RATE,
                            mean_initial_10_loss=float(np.mean(losses[:10])),
                            mean_final_10_loss=float(np.mean(losses[-10:])),
                            distance_pagerank_spearman=correlation(list(distance),
                                                                   [scores[n] for n in nodes], spearmanr)))
    write_csv(output / "poincare_embedding.csv", rows)
    write_csv(output / "poincare_fit.csv", fit)


def analyze_perturbations(graphs, references, output):
    removal, edge_trials, edge_summary = [], [], []
    for label in ("baseline", "section_230", "c1_baseline", "c1_section_230"):
        graph = graphs[label]
        nodes = sorted(graph)
        score = pagerank(graph)
        base = references[label]
        rng = np.random.default_rng(23021)
        orders = {"pagerank": [order(score)], "in_degree": [sorted(nodes, key=lambda n: (-graph.in_degree(n), n))],
                  "random": [list(rng.permutation(nodes)) for _ in range(100)]}
        for method, candidates in orders.items():
            for trial, removal_order in enumerate(candidates):
                for k in range(len(nodes) + 1):
                    sub = graph.subgraph(removal_order[k:])
                    largest = max(map(len, nx.weakly_connected_components(sub)), default=0)
                    removal.append(dict(graph=label, method=method, trial=trial, removed=k,
                                        last_removed=removal_order[k - 1] if k else "",
                                        largest_weak_component=largest,
                                        component_share_initial=largest / len(graph),
                                        remaining_edges=sub.size()))
        edges = sorted(graph.edges)
        for fraction in (0.05, 0.10, 0.20, 0.30):
            trials = []
            for seed in communities.SEEDS:
                rng = np.random.default_rng(seed)
                drop = rng.choice(len(edges), size=round(fraction * len(edges)), replace=False)
                sub = graph.copy()
                sub.remove_edges_from(edges[i] for i in drop)
                changed = pagerank(sub)
                groups, _ = leiden(sub)
                row = dict(graph=label, fraction=fraction, seed=seed, edges_removed=len(drop),
                           kendall_tau_b=rank_agreement(score, changed), community_nmi=partition_nmi(base, groups),
                           top_five_overlap=len(set(order(score)[:5]) & set(order(changed)[:5])))
                trials.append(row)
            edge_trials.extend(trials)
            edge_summary.append(dict(graph=label, fraction=fraction, trials=len(trials),
                                     mean_rank_tau=float(np.mean([r["kendall_tau_b"] for r in trials])),
                                     min_rank_tau=min(r["kendall_tau_b"] for r in trials),
                                     mean_partition_nmi=float(np.mean([r["community_nmi"] for r in trials])),
                                     mean_top_five_overlap=float(np.mean([r["top_five_overlap"] for r in trials]))))
    write_csv(output / "node_removal.csv", removal)
    write_csv(output / "edge_removal_trials.csv", edge_trials)
    write_csv(output / "edge_removal_summary.csv", edge_summary)

if __name__ == "__main__":
    output = analysis_output(__doc__)
    _, _, _, _, graphs, _ = load_corpus()
    references = {label: leiden(graph)[0] for label, graph in graphs.items()}
    analyze_perturbations(graphs, references, output)
    analyze_embeddings(graphs, output)
