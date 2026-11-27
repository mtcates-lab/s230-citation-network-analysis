"""Verify the coded dataset and its regenerated graph exports."""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

import networkx as nx

from _data import COURT_USE, ROOT, indexed, input_hashes, load_corpus, read_csv

EXPECTED_GRAPHS = {
    "baseline": (56, 317), "section_230": (56, 310),
    "c1_baseline": (43, 269), "c1_section_230": (43, 266),
    "resolved_c1_baseline": (42, 256), "resolved_c1_section_230": (42, 253),
    "c1_perfect10_baseline": (44, 273), "c1_perfect10_section_230": (44, 269),
    "full_reporter": (56, 306), "baseline_without_stubhub_erie": (54, 311),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_edge_sources(opinions, passages, evidence, output):
    boundaries = indexed(read_csv(ROOT / "validation/opinion_boundaries.csv"), "opinion_id")
    audited = indexed(read_csv(ROOT / "validation/passage_opinion_parts.csv"), "passage_id")
    pairs = {(r["citing_opinion_id"], r["cited_opinion_id"]): r
             for r in read_csv(ROOT / "data/citation_pairs.csv")}
    exported = {(r["citing_opinion_id"], r["cited_opinion_id"]): r
                for r in read_csv(output / "edge_evidence.csv")}
    require(boundaries.keys() == opinions.keys() and audited.keys() == passages.keys(),
            "Missing opinion or passage boundary records")
    require(pairs.keys() == exported.keys() and len(exported) == len(evidence),
            "Exported edge evidence does not match the pair ledger")

    all_pair_passages = defaultdict(set)
    for passage_id, passage in passages.items():
        if passage["cited_opinion_id"]:
            all_pair_passages[passage["citing_opinion_id"], passage["cited_opinion_id"]].add(passage_id)
    texts = {}
    for boundary in boundaries.values():
        source = boundary["source_file"]
        if source not in texts:
            texts[source] = (ROOT / source).read_text(encoding="utf-8").split("\n")

    for edge in evidence:
        source_id, target_id = edge["citing_opinion_id"], edge["cited_opinion_id"]
        pair = pairs[source_id, target_id]
        record = exported[source_id, target_id]
        baseline_ids = edge["baseline_passage_ids"].split()
        statutory_ids = edge["section_230_passage_ids"].split()
        require(all(record[key] == str(value) for key, value in edge.items()),
                f"Exported supporting IDs or flags differ for {source_id}, {target_id}")
        ledger_ids = set(pair["passage_ids"].split())
        require(ledger_ids == all_pair_passages[source_id, target_id]
                and set(baseline_ids) == {pid for pid in ledger_ids
                                          if passages[pid]["citing_use"] == COURT_USE}
                and set(statutory_ids) == set(pair["section_230_support_passages"].split()),
                f"Pair-ledger support differs for {source_id}, {target_id}")

        for passage_id in baseline_ids:
            passage = passages[passage_id]
            audit = audited[passage_id]
            boundary = boundaries[source_id]
            source_file = boundary["source_file"]
            line_number = int(audit["source_line"])
            first, last = (int(boundary[key]) for key in ("controlling_start_line", "controlling_end_line"))
            separate = boundary["separate_opinion_start_line"]
            delimiter = boundary["separate_opinion_delimiter"]
            require(passage["coding_status"] == "Coded" and passage["citing_use"] == COURT_USE
                    and audit["opinion_part"] == "Controlling opinion"
                    and audit["source_file"] == source_file
                    and passage["source_locator_file"] in (
                        source_file, "Combined working opinion text"
                        if source_file.endswith("/combined_opinions.txt") else source_file)
                    and audit["source_line"] == passage["citing_source_line"]
                    and (audit["citing_opinion_id"], audit["cited_opinion_id"]) == (source_id, target_id)
                    and 1 <= first <= line_number <= last <= len(texts[source_file]),
                    f"Invalid controlling-text source for {passage_id}")
            line = texts[source_file][line_number - 1]
            if separate and line_number >= int(separate):
                require(line_number == int(separate) and delimiter and delimiter in line,
                        f"Separate-opinion citation used for {passage_id}")
                line = line.split(delimiter, 1)[0]
            anchor = " ".join(audit["supporting_text"].split())
            require(anchor and anchor in " ".join(line.split()),
                    f"Controlling text does not contain the recorded anchor for {passage_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    directory = args.output
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    opinions, issues, passages, evidence, graphs, _ = load_corpus()
    require((len(opinions), len(issues), len(passages), len(evidence)) == (56, 75, 825, 318),
            "Unexpected input totals for the 56-opinion dataset")
    verify_edge_sources(opinions, passages, evidence, directory)
    screening = read_csv(ROOT / "validation" / "candidate_screening.csv")
    require(len(screening) == 217 and all(r["screening_decision"] in {"Include", "Exclude", "Duplicate"}
                                        for r in screening), "Incomplete candidate screening")
    require(all("recommended_action" not in r for r in screening), "Obsolete screening column")
    require(summary["dataset"] == "s230-appellate-56", "Wrong dataset identifier")
    require(not (ROOT / "validation" / "proposed_inclusion.csv").exists(),
            "Integrated opinion still marked as proposed")
    require(summary["input_sha256"] == input_hashes(), "Results do not match the input hashes")
    lexis_screen = read_csv(ROOT / "validation" / "lexis_appellate_screening.csv")
    lexis_reference = read_csv(ROOT / "validation" / "lexis_eligible_opinions.csv")
    included_lexis_entries = {r["pdf_entry"] for r in lexis_screen if r["screening_decision"] == "Include"}
    require(len(lexis_screen) == len({r["pdf_entry"] for r in lexis_screen}) == 215
            and len(lexis_reference) == len(included_lexis_entries) == 56
            and included_lexis_entries == {r["pdf_entry"] for r in lexis_reference},
            "Lexis screening and reference lists differ")
    require(all(not r["courtlistener_screening_cluster_id"] or
                (r["courtlistener_screening_cluster_id"] in {row["cluster_id"] for row in screening}
                 and r["evidence_locator"]) for r in lexis_screen),
            "Unresolved court screening reference in the Shepard’s table")
    require({r["opinion_id"]: r["reporter_citation"] for r in lexis_reference}
            == {key: row["reporter_citation"] for key, row in opinions.items()},
            "Lexis reporter crosswalk differs from the included opinions")
    case_recall = json.loads((ROOT / "data" / "lexis_case_recall.json").read_text(encoding="utf-8"))
    require(case_recall == dict(reference_positives=56, recovered=56, observed_in_scope=56,
                                recall_in_reference=1.0, missed=[], mode="case"),
            "Unexpected Lexis case coverage")
    require(summary["candidate_export"]["records"] == 217, "Wrong candidate snapshot")
    require(summary["candidate_export"]["date_counts"]["Within window"] == 207, "Wrong date filter")
    for entry in summary["graph_summary"]:
        label = entry["graph"]
        graph = graphs[label]
        require(EXPECTED_GRAPHS[label] == (len(graph), graph.size()), f"Wrong totals for {label}")
        require(EXPECTED_GRAPHS[label] == (entry["opinions"], entry["edges"]), f"Wrong summary for {label}")
        require(entry["top_five_ids"].split()[0] == "S230-001", f"Unexpected PageRank leader for {label}")
        filename = "s230_graph.graphml" if label == "baseline" else f"{label}.graphml"
        restored = nx.read_graphml(directory / filename)
        require(restored.is_directed() and set(restored) == set(graph)
                and set(restored.edges) == set(graph.edges), f"Export mismatch: {filename}")
    require(len(summary["graph_summary"]) == len(EXPECTED_GRAPHS)
            and {r["graph"] for r in summary["graph_summary"]} == EXPECTED_GRAPHS.keys(),
            "Missing or repeated graph summary")
    require(math.isclose(summary["highest_baseline_pagerank"], 0.1909471211907165, abs_tol=1e-10),
            "Unexpected baseline PageRank")
    for period, expected in (("before", (23, 17, 4, 2)), ("since", (19, 8, 8, 3))):
        row = next(r for r in summary["outcome_counts"]
                   if r["scope"] == "resolved c1 publisher or source" and r["period"] == period)
        require(tuple(row[k] for k in ("resolved_denominator", "all_barred", "none_barred", "mixed"))
                == expected, f"Wrong c1 denominators or outcomes for {period}")
    broader = {r["period"]: r for r in summary["outcome_counts"]
               if r["scope"] == "resolved c1 including publisher-based preemption"}
    for period, expected in (("before", (24, 17, 5, 2)), ("since", (21, 8, 10, 3))):
        require(tuple(broader[period][key] for key in
                      ("resolved_denominator", "all_barred", "none_barred", "mixed")) == expected,
                f"Wrong broader outcome counts for {period}")
    comparison = read_csv(directory / "publisher_outcome_comparison.csv")
    require(len(comparison) == len(opinions) and
            {r["opinion_id"] for r in comparison if r["changes_denominator"] == "1"} ==
            {"S230-016", "S230-029", "S230-045"}, "Wrong preemption boundary cases")
    chronology = indexed(read_csv(directory / "pagerank_chronology.csv"), "opinion_id")
    z = chronology["S230-001"]
    require(chronology.keys() == opinions.keys() and z["null_first_place_trials"] == z["trials"] == "500"
            and math.isclose(float(z["null_upper_975"]), 0.18727711, rel_tol=1e-6),
            "Unexpected PageRank chronology benchmark")
    circuit_pairs = read_csv(directory / "baseline_circuit_period_comparison.csv")
    matched = {(r["court_a"], r["court_b"]) for r in circuit_pairs if r["minimum_both"] == "1"}
    require(matched == {("ca2", "ca9")} and all(r["strict_both"] == "0" for r in circuit_pairs),
            "Unexpected matched circuit pairs")
    partitions = indexed(read_csv(directory / "leiden_partition_comparison.csv"), "partition")
    require({name: int(r["groups"]) for name, r in partitions.items()
             if name in {"reference", "directed"}} == {"reference": 4, "directed": 5}
            and math.isclose(float(partitions["directed"]["nmi_with_reference"]), .80773975),
            "Unexpected directed partition comparison")
    annual = read_csv(directory / "temporal_snapshots.csv")
    require(len(annual) == 116, "Incomplete annual snapshots")
    pooled = next(r for r in summary["circuit_divergence"]
                  if r["graph"] == "baseline" and r["period"] == "pooled" and r["threshold"] == "minimum")
    require(pooled["eligible_pairs"] == 55 and math.isclose(pooled["mean_bits"], 0.4615131556361183),
            "Unexpected pooled circuit divergence")
    require(len(read_csv(directory / "leiden_runs.csv")) == 1300, "Incomplete Leiden runs")
    named = directory
    attributed = nx.read_gexf(named / "s230_graph_attributed.gexf")
    baseline = graphs["baseline"]
    require(attributed.is_directed() and set(attributed) == set(baseline)
            and set(attributed.edges) == set(baseline.edges), "Attributed graph differs from the baseline")
    metrics = {r["opinion_id"]: r for r in read_csv(named / "s230_metrics.csv")
               if r["graph"] == "baseline"}
    communities = {r["opinion_id"]: r for r in read_csv(directory / "community_membership.csv")
                   if r["graph"] == "baseline"}
    for n, attrs in attributed.nodes(data=True):
        require(attrs["community"] == int(communities[n]["reference_group"])
                and attrs["consensus_group"] == int(communities[n]["consensus_group"])
                and attrs["in_degree"] == baseline.in_degree(n)
                and attrs["out_degree"] == baseline.out_degree(n)
                and math.isclose(attrs["pagerank"], float(metrics[n]["pagerank"]), abs_tol=1e-15),
                f"Attributed graph metrics do not match at {n}")
    parser_files = [named / f"eyecite_{kind}.json" for kind in ("results", "edges")]
    if any(p.exists() for p in parser_files):
        inventory, candidates = [json.loads(p.read_text(encoding="utf-8")) for p in parser_files]
        parsed = inventory["parsed_opinions"]
        require({entry["citing_opinion_id"] for entry in parsed} == opinions.keys()
                and len(parsed) == 56, "Wrong parser inventory")
        require(inventory["citation_tokens"] == sum(len(entry["tokens"]) for entry in parsed),
                "Wrong parser token count")
        pairs = candidates["pairs"]
        pair_ids = {(r["citing_opinion_id"], r["cited_opinion_id"]) for r in pairs}
        require(len(pair_ids) == len(pairs) == candidates["candidate_pairs"]
                and candidates["overlap_with_audited_baseline"] == len(pair_ids & set(baseline.edges))
                and all(r["in_audited_baseline"] == ((r["citing_opinion_id"], r["cited_opinion_id"]) in baseline.edges)
                        for r in pairs), "Wrong parser pair counts")
    print("Verified the 56-opinion snapshot, all ten graph exports, and the headline results.")


if __name__ == "__main__":
    main()
