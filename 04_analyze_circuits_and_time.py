"""Compute circuit divergence, citation opportunity, and temporal snapshots."""

from collections import Counter
from datetime import date
from importlib import import_module
from itertools import combinations, permutations

import networkx as nx
import numpy as np
from scipy.spatial.distance import jensenshannon

from _data import CUTOFF, END, analysis_output, load_corpus, write_csv

metrics = import_module("02_compute_metrics")
pagerank = metrics.pagerank
rank = metrics.rank

def gini(values):
    a = np.sort(np.asarray(list(values), dtype=float))
    return float(np.dot(2 * np.arange(1, len(a) + 1) - len(a) - 1, a) / (len(a) * a.sum()))


def analyze_time(graphs, opinions, output, partition):
    snapshots, history, opportunities = [], [], []
    z = next(n for n, row in opinions.items() if row["reporter_citation"] == "129 F.3d 327")
    for label, graph in graphs.items():
        if label not in {"baseline", "section_230", "c1_baseline", "c1_section_230"}:
            continue
        for year in range(1997, 2026):
            cutoff = f"{year}-12-31"
            nodes = sorted(n for n in graph if opinions[n]["decision_date"] <= cutoff)
            h = nx.DiGraph()
            h.add_nodes_from(nodes)
            h.add_edges_from(sorted(graph.subgraph(nodes).edges))
            if not nodes:
                continue
            possible = sum(opinions[s]["decision_date"] > opinions[t]["decision_date"]
                           for s, t in permutations(nodes, 2))
            scores = pagerank(h)
            top = [n for n in nodes if rank(scores, n) == 1]
            groups, _ = partition(h)
            snapshots.append(dict(graph=label, cutoff=cutoff, opinions=len(h), edges=h.size(),
                                  possible_prior_opinion_edges=possible,
                                  density_by_opportunity=h.size() / possible if possible else None,
                                  isolates=nx.number_of_isolates(h),
                                  weak_components=nx.number_weakly_connected_components(h),
                                  pagerank_gini=gini(scores.values()), leiden_communities=len(set(groups)),
                                  top_ids=" ".join(top), zeran_rank=rank(scores, z) if z in h else None))
            history.extend(dict(graph=label, cutoff=cutoff, opinion_id=n, pagerank=scores[n],
                                rank=rank(scores, n)) for n in nodes)
        for n in sorted(graph):
            dt = date.fromisoformat(opinions[n]["decision_date"])
            try:
                end = dt.replace(year=dt.year + 5)
            except ValueError:
                end = dt.replace(year=dt.year + 5, day=28)
            if end.isoformat() > END:
                continue
            for cohort, same_circuit in (("all", False), ("same circuit", True)):
                eligible = [m for m in graph if dt.isoformat() < opinions[m]["decision_date"] <= end.isoformat()
                            and (not same_circuit or opinions[m]["circuit"] == opinions[n]["circuit"])]
                observed = sum(graph.has_edge(m, n) for m in eligible)
                opportunities.append(dict(graph=label, opinion_id=n, cohort=cohort, cutoff=end.isoformat(),
                                          eligible_citing_opinions=len(eligible), observed_citations=observed,
                                          rate=observed / len(eligible) if eligible else None))
    write_csv(output / "temporal_snapshots.csv", snapshots)
    write_csv(output / "year_end_pagerank.csv", history)
    write_csv(output / "five_year_opportunity.csv", opportunities)


def circuit_pairs(graph, opinions, citing, targets, label, period):
    cite_by_court = {c: {n for n in citing if opinions[n]["circuit"] == c}
                     for c in sorted({opinions[n]["circuit"] for n in citing})}
    counts = {}
    for court, sources in cite_by_court.items():
        matching = [(s, t) for s, t in graph.edges if s in sources and t in targets]
        counts[court] = (len(sources), len({s for s, t in matching}), Counter(t for s, t in matching))
    rows = []
    for a, b in combinations(counts, 2):
        na, sa, ca = counts[a]
        nb, sb, cb = counts[b]
        ea, eb = ca.total(), cb.total()
        bits = None
        if ea and eb:
            bits = float(jensenshannon([ca[t] for t in targets], [cb[t] for t in targets], base=2) ** 2)
        rows.append(dict(graph=label, period=period, court_a=a, court_b=b, targets=len(targets),
                         opinions_a=na, opinions_b=nb, citing_opinions_a=sa, citing_opinions_b=sb,
                         edges_a=ea, edges_b=eb, jsd_bits=bits,
                         minimum=int(min(sa, sb) >= 2 and min(ea, eb) >= 5),
                         strict=int(min(sa, sb) >= 3 and min(ea, eb) >= 10)))
    return rows


def analyze_circuits(graphs, opinions, output):
    all_rows, annual, flows, summary = [], [], [], []
    for label, graph in graphs.items():
        before = sorted(n for n in graph if opinions[n]["decision_date"] < CUTOFF)
        since = sorted(set(graph) - set(before))
        scenarios = {"pooled": sorted(graph), "before_fixed_targets": before, "since_fixed_targets": since}
        comparison = {}
        for period, citing in scenarios.items():
            targets = sorted(graph) if period == "pooled" else before
            rows = circuit_pairs(graph, opinions, citing, targets, label, period)
            all_rows.extend(rows)
            comparison[period] = {(r["court_a"], r["court_b"]) for r in rows if r["minimum"]}
            for threshold in ("minimum", "strict"):
                scores = [r["jsd_bits"] for r in rows if r[threshold]]
                summary.append(dict(graph=label, period=period, threshold=threshold, eligible_pairs=len(scores),
                                    mean_bits=float(np.mean(scores)) if scores else None,
                                    min_bits=min(scores) if scores else None, max_bits=max(scores) if scores else None))
        common = comparison["before_fixed_targets"] & comparison["since_fixed_targets"]
        for row in all_rows:
            if row["graph"] == label:
                row["eligible_in_both_eras"] = int(row["period"] != "pooled"
                                                   and (row["court_a"], row["court_b"]) in common)
        if label not in {"baseline", "section_230", "c1_baseline", "c1_section_230"}:
            continue
        for year in range(1997, 2026):
            sources = sorted(n for n in graph if opinions[n]["decision_date"].startswith(str(year)))
            targets = sorted(n for n in graph if opinions[n]["decision_date"] <= f"{year}-12-31")
            annual.extend(circuit_pairs(graph, opinions, sources, targets, label, str(year)))
        courts = sorted({opinions[n]["circuit"] for n in graph})
        slices = {"pooled": sorted(graph), "before": before, "since": since}
        for period, sources in slices.items():
            sset = set(sources)
            count = Counter((opinions[s]["circuit"], opinions[t]["circuit"]) for s, t in graph.edges if s in sset)
            flows.extend(dict(graph=label, period=period, citing_court=a, cited_court=b,
                              edges=count[a, b]) for a in courts for b in courts)
    write_csv(output / "circuit_divergence.csv", all_rows)
    write_csv(output / "circuit_divergence_annual.csv", annual)
    write_csv(output / "circuit_flows.csv", flows)
    write_csv(output / "circuit_divergence_summary.csv", summary)
    return summary



if __name__ == "__main__":
    output = analysis_output(__doc__)
    opinions, _, _, _, graphs, _ = load_corpus()
    analyze_time(graphs, opinions, output, import_module("03_analyze_communities").leiden)
    analyze_circuits(graphs, opinions, output)
