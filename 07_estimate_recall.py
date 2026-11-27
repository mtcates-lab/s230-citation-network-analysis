"""Measure recovery against an independently enumerated reference list."""

import argparse
from pathlib import Path

from _data import load_corpus, read_csv, write_json


def measure(reference, observed):
    if not reference:
        raise ValueError("No reference positives")
    overlap = reference & observed
    return {"reference_positives": len(reference), "recovered": len(overlap),
            "observed_in_scope": len(observed), "recall_in_reference": len(overlap) / len(reference),
            "missed": sorted(reference - observed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("case", "edge"))
    parser.add_argument("reference", type=Path)
    parser.add_argument("--sample", type=Path,
                        help="Edge mode: independent ledger of completely checked citing opinions")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    opinions, _, _, _, graphs, _ = load_corpus()
    rows = read_csv(args.reference)
    if args.mode == "case":
        reference = {r["reporter_citation"].strip() for r in rows}
        if args.sample or "" in reference or len(reference) != len(rows):
            parser.error("Case mode requires unique nonempty operative reporter citations and no --sample")
        observed = {r["reporter_citation"] for r in opinions.values()}
        result = measure(reference, observed)
    else:
        if not args.sample:
            parser.error("Edge mode requires --sample with one citing_opinion_id per audited opinion")
        sample_rows = read_csv(args.sample)
        sample = {r["citing_opinion_id"] for r in sample_rows}
        if not sample or len(sample) != len(sample_rows) or not sample <= opinions.keys():
            parser.error("Sample must contain unique included citing opinions")
        reference = {(r["citing_opinion_id"], r["cited_opinion_id"]) for r in rows}
        if len(reference) != len(rows) or any(s not in sample or t not in opinions or
                opinions[s]["decision_date"] <= opinions[t]["decision_date"] for s, t in reference):
            parser.error("Invalid reference edge or citing opinion outside the sample")
        result = measure(reference, {(s, t) for s, t in graphs["baseline"].edges if s in sample})
        result["sample_opinions"] = len(sample)
        result["by_citing_opinion"] = []
        for s in sorted(sample):
            refs = {pair for pair in reference if pair[0] == s}
            found = {(a, b) for a, b in graphs["baseline"].edges if a == s}
            result["by_citing_opinion"].append(dict(citing_opinion_id=s, reference_positives=len(refs),
                                                   observed_edges=len(found), recovered=len(refs & found)))
    result["mode"] = args.mode
    write_json(args.output, result)


if __name__ == "__main__":
    main()
