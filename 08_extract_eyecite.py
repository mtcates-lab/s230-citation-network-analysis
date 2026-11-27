"""Produce a parser-level citation inventory from the working opinion text."""

import argparse
import hashlib
import logging
import re
import unicodedata
from bisect import bisect_right
from collections import Counter, defaultdict
from importlib.metadata import version
from pathlib import Path

from eyecite import get_citations, resolve_citations
from eyecite.models import FullCaseCitation

from _data import ROOT, read_csv, write_json

REPORTER_ALIASES = {
    "481 F.3d 751": "S230-007",
    "565 F.3d 560": "S230-011",
    "767 F.3d 894": "S230-021",
    "938 F.3d 1026": "S230-034",
}
RECOVERED = {"S230-013", "S230-016", "S230-028", "S230-041", "S230-055", "S230-056"}


def reporter_key(citation):
    return re.sub(r"[^a-z0-9]", "", citation.lower())


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‐", "-").replace("‑", "-")
    return " ".join(text.split())


def flatten(lines, first, last):
    if not 1 <= first <= last <= len(lines):
        raise ValueError(f"Invalid line range {first}–{last} for {len(lines)} source lines")
    starts, numbers, chunks = [], [], []
    offset = 0
    for n in range(first, last + 1):
        piece = normalize(lines[n - 1])
        if piece:
            starts.append(offset)
            numbers.append(n)
            chunks.append(piece)
            offset += len(piece) + 1
    return " ".join(chunks), starts, numbers


def extract(compilation, output):
    source = compilation.read_bytes()
    input_lines = source.decode("utf-8").split("\n")
    corpus = read_csv(ROOT / "data" / "included_opinions.csv")
    dates = {r["opinion_id"]: r["decision_date"] for r in corpus}
    reporters = {reporter_key(c): n for c, n in REPORTER_ALIASES.items()}
    reporters.update({reporter_key(r["reporter_citation"]): r["opinion_id"] for r in corpus})
    hashes = {"working_compilation": hashlib.sha256(source).hexdigest()}
    edges, observations = defaultdict(list), []
    for row in corpus:
        citing = row["opinion_id"]
        lines = input_lines
        if citing in RECOVERED:
            recovered = ROOT / "sources" / "recovered" / f"{int(citing[-3:])}.txt"
            raw = recovered.read_bytes()
            hashes[citing] = hashlib.sha256(raw).hexdigest()
            lines = raw.decode("utf-8").split("\n")
        first, last = [int(v) for v in row["source_lines"].split("–")]
        text, starts, numbers = flatten(lines, first, last)
        citations = get_citations(text)
        resolved = {}
        for resource, matches in resolve_citations(citations).items():
            token = getattr(resource, "citation", None)
            if isinstance(token, FullCaseCitation):
                key = reporter_key(token.matched_text())
                if key in reporters:
                    resolved.update({match.span(): reporters[key] for match in matches})
        tokens = []
        for token in citations:
            start, finish = token.span()
            parsed = text[start:finish]
            target = resolved.get((start, finish))
            if isinstance(token, FullCaseCitation):
                target = reporters.get(reporter_key(token.matched_text()), target)
            line = numbers[bisect_right(starts, start) - 1]
            kind = type(token).__name__
            prior = bool(target and dates[target] < dates[citing])
            tokens.append(dict(source_line=line, citation_type=kind, citation=parsed,
                               potential_cited_opinion_id=target, chronological_candidate=prior))
            if prior:
                edges[citing, target].append(dict(source_line=line, citation_type=kind, citation=parsed))
        observations.append(dict(citing_opinion_id=citing, line_start=first, line_end=last,
                                 token_counts=dict(sorted(Counter(r["citation_type"] for r in tokens).items())),
                                 tokens=tokens))
    retained = {(r["citing_opinion_id"], r["cited_opinion_id"])
                for r in read_csv(ROOT / "data" / "citation_pairs.csv")
                if r["evidence_for_baseline_graph"] == "yes"}
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "eyecite_results.json",
               dict(eyecite_version=version("eyecite"), reporters_db_version=version("reporters-db"),
                    input_sha256=hashes, opinions=len(observations),
                    citation_tokens=sum(len(r["tokens"]) for r in observations), parsed_opinions=observations))
    write_json(output / "eyecite_edges.json",
               dict(status="parser_candidates", candidate_pairs=len(edges), audited_baseline_pairs=len(retained),
                    overlap_with_audited_baseline=len(set(edges) & retained),
                    pairs=[dict(citing_opinion_id=s, cited_opinion_id=t,
                                in_audited_baseline=(s, t) in retained, parser_hits=hits)
                           for (s, t), hits in sorted(edges.items())]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compilation", type=Path, help="Working plain-text opinion compilation")
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    logging.getLogger("eyecite").setLevel(logging.ERROR)
    extract(args.compilation, args.output)


if __name__ == "__main__":
    main()
