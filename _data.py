"""Read the coded data and reproduce the audited directed graphs."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parent
CUTOFF = "2018-04-11"
OUTCOMES = ("All barred", "None barred", "Mixed")
START, END = "1997-11-12", "2025-12-31"
COURT_USE = "Court’s own discussion"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if not reader.fieldnames or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Malformed CSV: {path}")
    return rows


def write_csv(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def indexed(rows, field):
    index = {row[field]: row for row in rows}
    if "" in index or len(index) != len(rows):
        raise ValueError(f"Missing or duplicate {field}")
    return index


def outcome(codes):
    if {"B", "N"} <= codes:
        return "Mixed"
    if "B" in codes:
        return "All barred"
    if "N" in codes:
        return "None barred"
    return "No resolved claim outcome"


def load_corpus():
    directory = ROOT / "data"
    opinions = indexed(read_csv(directory / "included_opinions.csv"), "opinion_id")
    issues = indexed(read_csv(directory / "issues.csv"), "issue_id")
    passages = indexed(read_csv(directory / "citation_passages.csv"), "passage_id")
    audits = read_csv(directory / "citation_pairs.csv")
    fosta = read_csv(directory / "fosta.csv")
    by_opinion = defaultdict(list)
    for row in issues.values():
        n = row["opinion_id"]
        if n not in opinions or row["result_code"] not in {"B", "N", "S", "U"}:
            raise ValueError(f"Invalid issue {row['issue_id']}")
        by_opinion[n].append(row)

    c1, resolved = set(), set()
    for n, row in opinions.items():
        dt = row["decision_date"]
        date.fromisoformat(dt)
        principal = issues[row["principal_issue_id"]]
        if not START <= dt <= END or principal["opinion_id"] != n or not row["inclusion_reason"]:
            raise ValueError(f"Invalid inclusion row {n}")
        relevant = by_opinion[n]
        if int(row["number_of_issue_entries"]) != len(relevant):
            raise ValueError(f"Issue count mismatch for {n}")
        outcome_all = outcome({r["result_code"] for r in relevant})
        if outcome_all != "No resolved claim outcome" and outcome_all != row["statutory_claim_outcome"]:
            raise ValueError(f"Statutory claim outcome mismatch for {n}")
        scoped = {r["result_code"] for r in relevant if r["distinct_c1_issue"] == "yes"}
        row["derived_claim_outcome"] = outcome_all
        row["derived_c1_outcome"] = outcome(scoped)
        expected = row["c1_claim_outcome"].replace(
            "No claim-level protection outcome coded", "No resolved claim outcome")
        if row["derived_c1_outcome"] != expected:
            raise ValueError(f"Section 230(c)(1) claim outcome mismatch for {n}")
        if any(r["distinct_c1_issue"] in {"yes", "scope"} for r in relevant):
            c1.add(n)
        if row["derived_c1_outcome"] in OUTCOMES:
            resolved.add(n)
    if c1 != {n for n in opinions if opinions[n]["restricted_c1_graph"] == "yes"}:
        raise ValueError("Restricted membership disagrees with issue coding")
    if resolved != {n for n in opinions if opinions[n]["direct_c1_claim_graph"] == "yes"}:
        raise ValueError("Resolved membership disagrees with issue coding")

    graph = nx.DiGraph()
    for n, row in sorted(opinions.items()):
        graph.add_node(n, case_name=row["case_name"], circuit=row["circuit"],
                       decision_date=row["decision_date"], reporter=row["reporter_citation"],
                       c1_outcome=row["derived_c1_outcome"])
    grouped = defaultdict(list)
    for row in passages.values():
        s, t = row["citing_opinion_id"], row["cited_opinion_id"]
        if s not in opinions or (t and t not in opinions):
            raise ValueError(f"Invalid passage endpoints at {row['passage_id']}")
        if row["material_to_section_230"] == "yes" and row["citing_use"] != COURT_USE:
            raise ValueError(f"Noncourt passage coded as statutory reasoning: {row['passage_id']}")
        if row["coding_status"] not in {"Coded", "Excluded source artifact"}:
            raise ValueError(f"Invalid coding status at {row['passage_id']}")
        if t:
            grouped[s, t].append(row)

    audited_pairs = {(r["citing_opinion_id"], r["cited_opinion_id"]): r for r in audits}
    if len(audited_pairs) != len(audits) or audited_pairs.keys() != grouped.keys():
        raise ValueError("Pair ledger does not match passage endpoints")

    statutory, reporter = graph.copy(), graph.copy()
    edge_rows = []
    for (s, t), rows in sorted(grouped.items()):
        court_rows = [r for r in rows if r["citing_use"] == COURT_USE]
        statutory_rows = [r for r in court_rows if r["material_to_section_230"] == "yes"]
        full_rows = [r for r in court_rows if r["match_method"] == "Full reporter match"]
        ledger = audited_pairs[s, t]
        if (bool(court_rows) != (ledger["evidence_for_baseline_graph"] == "yes") or
                bool(statutory_rows) != (ledger["evidence_for_section_230_graph"] == "yes")):
            raise ValueError(f"Audit decisions do not match the passage flags: {s}, {t}")
        if court_rows:
            if opinions[s]["decision_date"] <= opinions[t]["decision_date"]:
                raise ValueError(f"Nonretrospective edge: {s}, {t}")
            graph.add_edge(s, t)
        if statutory_rows:
            statutory.add_edge(s, t)
        if full_rows:
            reporter.add_edge(s, t)
        edge_rows.append(dict(citing_opinion_id=s, cited_opinion_id=t,
                              candidate_passages=len(rows), baseline=int(bool(court_rows)),
                              section_230=int(bool(statutory_rows)), full_reporter=int(bool(full_rows)),
                              baseline_passage_ids=" ".join(r["passage_id"] for r in court_rows),
                              section_230_passage_ids=" ".join(r["passage_id"] for r in statutory_rows)))
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Baseline graph is not acyclic")

    perfect10 = next(n for n, r in opinions.items() if r["reporter_citation"] == "488 F.3d 1102")
    graphs = {
        "baseline": graph,
        "section_230": statutory,
        "c1_baseline": graph.subgraph(c1),
        "c1_section_230": statutory.subgraph(c1),
        "resolved_c1_baseline": graph.subgraph(resolved),
        "resolved_c1_section_230": statutory.subgraph(resolved),
        "c1_perfect10_baseline": graph.subgraph(c1 | {perfect10}),
        "c1_perfect10_section_230": statutory.subgraph(c1 | {perfect10}),
        "full_reporter": reporter,
        "baseline_without_stubhub_erie": graph.subgraph(
            [n for n, r in opinions.items() if r["reporter_citation"] not in {"624 F.3d 363", "925 F.3d 135"}]),
    }
    return opinions, issues, passages, edge_rows, graphs, fosta


def audit_search(opinions, output):
    """Match candidate records by ID or exact reporter and join screening decisions."""
    path = ROOT / "data" / "courtlistener_candidates.tsv"
    by_id = {r["courtlistener_cluster_id"]: n for n, r in opinions.items() if r["courtlistener_cluster_id"]}
    by_reporter = {r["reporter_citation"]: n for n, r in opinions.items()}
    by_court_date = defaultdict(list)
    for n, r in opinions.items():
        by_court_date[r["circuit"], r["decision_date"]].append(n)
    matches = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        for row in reader:
            cluster = row[""]
            dt = datetime.strptime(row["date_filed"], "%m/%d/%Y").date().isoformat()
            window = "Before window" if dt < START else "After window" if dt > END else "Within window"
            reporters = {c.strip() for c in row["citation"].split(";")}
            linked_reporters = {by_reporter[c] for c in reporters if c in by_reporter}
            possible = by_court_date[row["court"], dt]
            linked = by_id.get(cluster, "")
            if linked:
                status = "Included cluster ID"
            elif len(linked_reporters) == 1 and next(iter(linked_reporters)) in possible:
                linked = next(iter(linked_reporters))
                status = ("Same court, date and reporter; possible duplicate"
                          if opinions[linked]["courtlistener_cluster_id"]
                          else "Same court, date and reporter; no canonical ID recorded")
            elif window != "Within window":
                status = "Outside study dates"
            else:
                status = "No confirmed inclusion match in this export"
            matches.append(dict(cluster_id=cluster, case_name=row["case_name"], court=row["court"],
                                date=dt, window=window, status=status, opinion_id=linked,
                                same_court_date_leads=" ".join(possible), source_url=row["absolute_url"]))
    indexed(matches, "cluster_id")
    screening_path = ROOT / "validation" / "candidate_screening.csv"
    if screening_path.exists():
        screening = indexed(read_csv(screening_path), "cluster_id")
        if screening.keys() != {row["cluster_id"] for row in matches}:
            raise ValueError("Screening ledger does not match the candidate export")
        for row in matches:
            row.update({key: value for key, value in screening[row["cluster_id"]].items()
                        if key not in row})
    write_csv(output / "candidate_crosswalk.csv", matches)
    return dict(records=len(matches), date_counts=Counter(r["window"] for r in matches),
                link_counts=Counter(r["status"] for r in matches),
                opinions_with_exact_id=len({r["opinion_id"] for r in matches if r["status"] == "Included cluster ID"}),
                opinions_with_id_or_reporter_match=len({r["opinion_id"] for r in matches if r["opinion_id"]}),
                opinions_without_id_or_reporter_match=sorted(set(opinions) - {r["opinion_id"] for r in matches}),
                included_opinion_ids_without_exact_id=sorted(set(opinions) - {
                    r["opinion_id"] for r in matches if r["status"] == "Included cluster ID"}))


def input_hashes():
    directory = ROOT / "data"
    inputs = ["included_opinions.csv", "issues.csv", "fosta.csv", "citation_passages.csv",
              "citation_pairs.csv", "courtlistener_candidates.tsv"]
    paths = [directory / name for name in inputs]
    paths += sorted(path for name in ("sources", "validation") for path in (ROOT / name).rglob("*"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if p.is_file()}


def analysis_output(description):
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    return output
