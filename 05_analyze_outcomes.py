"""Summarize coded outcomes and FOSTA comparisons."""

from collections import Counter, defaultdict
from datetime import date

from _data import CUTOFF, END, OUTCOMES, START, analysis_output, load_corpus, outcome, write_csv

PRIMARY = "resolved c1 publisher or source"
BROAD = "resolved c1 including publisher-based preemption"


def publisher_outcomes(opinions, issues, output):
    primary_codes, preemption = defaultdict(set), defaultdict(list)
    for issue in issues.values():
        opinion_id = issue["opinion_id"]
        if issue["distinct_c1_issue"] == "yes":
            primary_codes[opinion_id].add(issue["result_code"])
        effect = issue["publisher_preemption_effect"]
        if effect:
            if (effect not in {"B", "N"} or issue["result_code"] != "S"
                    or issue["distinct_c1_issue"] != "no"
                    or not {"c1", "e3"} <= set(issue["subsection"].split(","))
                    or issue["ruling_status"] != "Controlling holding"):
                raise ValueError(f"Invalid publisher-based preemption code: {issue['issue_id']}")
            preemption[opinion_id].append(issue)

    rows = []
    broad = {}
    for opinion_id, opinion in opinions.items():
        added = preemption[opinion_id]
        primary = opinion["derived_c1_outcome"]
        broad[opinion_id] = outcome(primary_codes[opinion_id] |
                                    {issue["publisher_preemption_effect"] for issue in added})
        rows.append(dict(opinion_id=opinion_id, case_name=opinion["case_name"],
                         decision_date=opinion["decision_date"], primary_outcome=primary,
                         broader_outcome=broad[opinion_id],
                         changes_denominator=int((primary in OUTCOMES) != (broad[opinion_id] in OUTCOMES)),
                         added_issue_ids=" | ".join(issue["issue_id"] for issue in added),
                         pinpoints=" | ".join(issue["reporter_pinpoint"] for issue in added),
                         rationale=" | ".join(issue["statutory_ruling"] for issue in added)))
    write_csv(output / "publisher_outcome_comparison.csv", rows)
    return broad


def analyze_outcomes(opinions, issues, fosta, output):
    broad = publisher_outcomes(opinions, issues, output)
    periods = {"before": (START, "2018-04-10"), "since": (CUTOFF, END)}
    span = date.fromisoformat(END) - date.fromisoformat(CUTOFF)
    equal_start = date.fromisoformat("2018-04-10") - span
    periods["equal_window_before"] = (equal_start.isoformat(), "2018-04-10")
    periods["1997–1999"] = (START, "1999-12-31")
    for y in range(2000, 2026, 5):
        periods[f"{y}–{min(y + 4, 2025)}"] = (f"{y}-01-01", f"{min(y + 4, 2025)}-12-31")
    direct_carveout = {row["opinion_id"] for row in fosta if row["question_type"] == "Direct carveout"}
    periods["since_excluding_direct_carveout"] = periods["since"]
    rows = []
    for period, (start, end) in periods.items():
        eligible = [r for r in opinions.values() if start <= r["decision_date"] <= end
                    and (period != "since_excluding_direct_carveout" or r["opinion_id"] not in direct_carveout)]
        courts = ["All courts"] + sorted({r["circuit"] for r in eligible})
        for court in courts:
            members = [r for r in eligible if court == "All courts" or r["circuit"] == court]
            for scope, counts in (
                ("all coded statutory questions", Counter(r["derived_claim_outcome"] for r in members)),
                (PRIMARY, Counter(r["derived_c1_outcome"] for r in members)),
                (BROAD, Counter(broad[r["opinion_id"]] for r in members)),
            ):
                denominator = sum(counts[x] for x in OUTCOMES)
                rows.append(dict(period=period, start=start, end=end, court=court, scope=scope,
                                 opinions=len(members), resolved_denominator=denominator,
                                 all_barred=counts["All barred"], none_barred=counts["None barred"],
                                 mixed=counts["Mixed"], no_resolved_claim=len(members) - denominator,
                                 share_all_barred=counts["All barred"] / denominator if denominator else None))
    write_csv(output / "outcomes.csv", rows)
    verified = []
    for row in fosta:
        case = opinions[row["opinion_id"]]
        if case["decision_date"] != row["opinion_date"]:
            raise ValueError(f"FOSTA date mismatch: {row['opinion_id']}")
        verified.append(dict(**row, case_name=case["case_name"], court=case["circuit"],
                             decision_period="before" if case["decision_date"] < CUTOFF else "since"))
    write_csv(output / "fosta_holdings.csv", verified)
    return [r for r in rows if r["period"] in ("before", "since") and r["court"] == "All courts"]


if __name__ == "__main__":
    output = analysis_output(__doc__)
    opinions, issues, _, _, _, fosta = load_corpus()
    analyze_outcomes(opinions, issues, fosta, output)
