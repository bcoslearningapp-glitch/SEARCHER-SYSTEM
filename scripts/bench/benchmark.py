"""Performance benchmark against a running stack (PRD §70, #57).

It seeds a personal-library-scale corpus of synthetic multilingual text sources through the public API, waits
for background ingestion, then measures the PRD §70 targets:
- project page load < 2 s;
- full-text search < 1 s;
- state-changing local API actions < 500 ms;
- ingestion runs in the background and reports its status.

Vector search is reported as not measured, because there is no vector index yet (see STATUS).

Usage (stack running, e.g. `docker compose up`):
    python scripts/bench/benchmark.py --works 200 --api http://localhost:8000 --web http://localhost:3000
Only the standard library is used, so it runs anywhere Python 3.12 does.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable
from typing import Any

WORDS = {
    "en": [
        "mentoring",
        "retention",
        "apprentice",
        "workshop",
        "cohort",
        "evidence",
        "second",
        "year",
        "decline",
        "trust",
        "guidance",
    ],
    "fr": [
        "tutorat",
        "rétention",
        "apprenti",
        "atelier",
        "cohorte",
        "preuve",
        "deuxième",
        "année",
        "déclin",
        "confiance",
    ],
    "ar": ["التوجيه", "الاستبقاء", "المتدرب", "الورشة", "الفوج", "الدليل", "السنة", "الثانية", "التراجع", "الثقة"],
}
QUERIES = ["mentoring retention", "cohorte déclin", "التوجيه الثقة", "apprentice workshop", "second year", "الفوج"]


def _request(method: str, url: str, body: Any = None, *, multipart: tuple[str, bytes] | None = None) -> Any:
    headers = {}
    data = None
    if multipart is not None:
        boundary = uuid.uuid4().hex
        name, payload = multipart
        data = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                "Content-Type: text/plain\r\n\r\n"
            ).encode()
            + payload
            + f"\r\n--{boundary}--\r\n".encode()
        )
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310 - benchmark target URL
    with urllib.request.urlopen(req, timeout=60) as response:  # noqa: S310
        raw = response.read()
    return json.loads(raw) if raw and response.headers.get_content_type() == "application/json" else raw


def _document(rng: random.Random, pages: int) -> bytes:
    paragraphs = []
    for _ in range(pages * 6):
        lang = rng.choice(list(WORDS))
        paragraphs.append(" ".join(rng.choice(WORDS[lang]) for _ in range(rng.randint(40, 90))))
    return ("\n\n".join(paragraphs)).encode()


def _timed(fn: Callable[[], Any], runs: int) -> list[float]:
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return samples


def _summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "p50_ms": round(statistics.median(ordered) * 1000, 1),
        "p95_ms": round(ordered[max(0, int(len(ordered) * 0.95) - 1)] * 1000, 1),
        "max_ms": round(ordered[-1] * 1000, 1),
    }


def seed(api: str, works: int, pages: int, rng: random.Random) -> tuple[str, list[str], float]:
    project = _request(
        "POST", f"{api}/api/v1/projects", {"title": "Benchmark", "initial_input": "x", "input_type": "IDEA"}
    )
    assets = []
    start = time.perf_counter()
    for i in range(works):
        work = _request(
            "POST", f"{api}/api/v1/sources", {"work": {"title": f"Benchmark work {i}"}, "project_id": project["id"]}
        )
        asset = _request(
            "POST",
            f"{api}/api/v1/sources/editions/{work['editions'][0]['id']}/assets",
            multipart=(f"work-{i}.txt", _document(rng, pages)),
        )
        assets.append(asset["id"])
    uploaded = time.perf_counter() - start
    return project["id"], assets, uploaded


def wait_for_ingestion(api: str, assets: list[str], timeout: float) -> tuple[float, dict[str, int]]:
    start = time.perf_counter()
    pending = set(assets)
    counts: dict[str, int] = {}
    while pending and time.perf_counter() - start < timeout:
        for asset_id in list(pending):
            status = _request("GET", f"{api}/api/v1/sources/assets/{asset_id}")["ingestion_status"]
            if status in ("COMPLETE", "FAILED", "NOT_APPLICABLE"):
                pending.discard(asset_id)
                counts[status] = counts.get(status, 0) + 1
        time.sleep(0.5)
    counts["PENDING"] = len(pending)
    return time.perf_counter() - start, counts


def measure(api: str, web: str, project_id: str, runs: int) -> dict[str, dict[str, float]]:
    search = iter(QUERIES * runs)
    results = {
        "full_text_search": _summary(
            _timed(lambda: _request("GET", f"{api}/api/v1/sources/search?q={urllib.parse.quote(next(search))}"), runs)
        ),
        "project_page_load": _summary(_timed(lambda: _request("GET", f"{web}/en/projects/{project_id}"), runs)),
        "project_sources_page_load": _summary(
            _timed(lambda: _request("GET", f"{web}/en/projects/{project_id}/sources"), runs)
        ),
        "library_page_load": _summary(_timed(lambda: _request("GET", f"{web}/en/library"), runs)),
        "state_change_create_claim": _summary(
            _timed(
                lambda: _request(
                    "POST",
                    f"{api}/api/v1/projects/{project_id}/claims",
                    {"statement": f"Claim {uuid.uuid4().hex[:8]}", "claim_type": "OBSERVATION"},
                ),
                runs,
            )
        ),
        "state_change_add_note": _summary(
            _timed(lambda: _request("POST", f"{api}/api/v1/projects/{project_id}/notes", {"body": "note"}), runs)
        ),
    }
    return results


TARGETS_MS = {
    "full_text_search": 1000,
    "project_page_load": 2000,
    "project_sources_page_load": 2000,
    "library_page_load": 2000,
    "state_change_create_claim": 500,
    "state_change_add_note": 500,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--web", default="http://localhost:3000")
    parser.add_argument("--works", type=int, default=200)
    parser.add_argument("--pages", type=int, default=5, help="approximate pages of text per work")
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--ingestion-timeout", type=float, default=900)
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    parser.add_argument("--measure-only", metavar="PROJECT_ID", help="skip seeding; measure an already seeded project")
    args = parser.parse_args()
    rng = random.Random(58)  # noqa: S311 - a deterministic synthetic corpus, not a secret
    if args.measure_only:
        project_id, upload_seconds, ingest_seconds, statuses = args.measure_only, 0.0, 0.0, {"skipped": 1}
    else:
        project_id, assets, upload_seconds = seed(args.api, args.works, args.pages, rng)
        ingest_seconds, statuses = wait_for_ingestion(args.api, assets, args.ingestion_timeout)
    timings = measure(args.api, args.web, project_id, args.runs)
    report = {
        "machine": {"python": platform.python_version(), "system": platform.platform(), "cpu": platform.processor()},
        "corpus": {"works": args.works, "pages_per_work": args.pages, "ingestion_status": statuses},
        "upload_seconds": round(upload_seconds, 1),
        "ingestion_seconds": round(ingest_seconds, 1),
        "timings": timings,
        "targets_ms": TARGETS_MS,
        "passed": {k: timings[k]["p95_ms"] <= TARGETS_MS[k] for k in TARGETS_MS},
        "not_measured": {"vector_search": "no vector index yet (PRD §61 SHOULD; tracked in STATUS)"},
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        corpus = "existing project (measure only)" if args.measure_only else f"{args.works} works x ~{args.pages} pages"
        print(f"corpus: {corpus}; ingestion {report['ingestion_seconds']} s {statuses}")
        for key, values in timings.items():
            verdict = "PASS" if report["passed"][key] else "MISS"
            p50, p95 = values["p50_ms"], values["p95_ms"]
            print(f"{key:28} p50 {p50:8.1f} ms  p95 {p95:8.1f} ms  target {TARGETS_MS[key]} ms  {verdict}")
    return 0 if all(report["passed"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
