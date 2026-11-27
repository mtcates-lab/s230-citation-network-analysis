"""Run the recorded CourtListener query and export a fresh candidate snapshot."""

import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import Request, urlopen

HOST = "www.courtlistener.com"
SEARCH_URL = f"https://{HOST}/api/rest/v4/search/"
QUERY = {
    "q": '"47 U.S.C. § 230" OR "47 U.S.C. 230" OR "section 230" OR "CDA 230"',
    "type": "o",
    "stat_Precedential": "on",
    "court": "scotus ca1 ca2 ca3 ca4 ca5 ca6 ca7 ca8 ca9 ca10 ca11 cadc cafc",
    "filed_after": "1996-01-01",
    "order_by": "dateFiled asc",
    "page_size": 20,
}


def fetch_all(token):
    url = f"{SEARCH_URL}?{urlencode(QUERY)}"
    results, visited = [], set()
    while url:
        link = urlsplit(url)
        if link.scheme != "https" or link.netloc != HOST or url in visited:
            raise ValueError("Unexpected or repeated pagination URL")
        visited.add(url)
        for attempt in range(4):
            request = Request(url, headers={"Accept": "application/json"})
            request.add_unredirected_header("Authorization", f"Token {token}")
            try:
                with urlopen(request, timeout=60) as reply:
                    payload = json.load(reply)
                break
            except HTTPError as exc:
                if exc.code != 429 or attempt == 3:
                    raise RuntimeError(f"CourtListener returned HTTP {exc.code}; collection stopped") from exc
                time.sleep(30)
        results.extend(payload["results"])
        print(f"Page {len(visited)}: {len(results)} candidate records so far")
        url = urljoin(url, payload["next"]) if payload["next"] else None
        if url:
            time.sleep(0.5)
    return results


def flatten(case):
    citations = case.get("citation") or []
    if isinstance(citations, str):
        citations = [citations]
    return dict(cluster_id=case.get("cluster_id"), case_name=case.get("caseName"),
                court=case.get("court_id") or case.get("court"), date_filed=case.get("dateFiled"),
                citation="; ".join(citations), docket_number=case.get("docketNumber"),
                judge=case.get("judge"), status=case.get("status"),
                absolute_url=urljoin(SEARCH_URL, case["absolute_url"]) if case.get("absolute_url") else "",
                snippet=(case.get("snippet") or "").replace("\n", " ").strip()[:300])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("retrieval_runs"))
    parser.add_argument("--show-query", action="store_true")
    args = parser.parse_args()
    if args.show_query:
        print(json.dumps(QUERY, indent=2, ensure_ascii=False))
        return
    token = os.environ.get("COURTLISTENER_TOKEN")
    if not token:
        parser.error("Set COURTLISTENER_TOKEN in the environment")
    pulled_at = datetime.now(timezone.utc)
    results = fetch_all(token)
    if not results:
        raise SystemExit("No candidates returned")
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = pulled_at.strftime("%Y%m%dT%H%M%S%fZ")
    raw = args.output / f"s230_raw_{stamp}.json"
    raw.write_text(json.dumps(dict(pulled_at=pulled_at.isoformat(), total_cases=len(results),
                                   query_params=QUERY, results=results), indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    rows = [flatten(row) for row in results]
    csv_path = args.output / f"s230_all_cases_{stamp}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} candidate records to {raw} and {csv_path}")


if __name__ == "__main__":
    main()
