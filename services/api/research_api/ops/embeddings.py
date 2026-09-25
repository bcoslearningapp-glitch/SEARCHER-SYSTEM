"""Embedding backfill for semantic retrieval (ADR-025).

Ingestion embeds new chunks when a provider is configured. This command catches up afterwards: after
enabling a provider, after changing the model, or after an embedding failure.

    python -m research_api.ops.embeddings backfill [--limit N]
    python -m research_api.ops.embeddings status
"""

from __future__ import annotations

import argparse
import sys

from research_api.config import get_settings
from research_api.modules.sources_library import semantic
from research_api.platform import embeddings
from research_api.platform.db import session_scope


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m research_api.ops.embeddings")
    commands = parser.add_subparsers(dest="command", required=True)
    backfill = commands.add_parser("backfill", help="embed chunks that have no vector for the configured model")
    backfill.add_argument("--limit", type=int, default=None)
    commands.add_parser("status", help="show how many chunks are embedded for the configured model")
    args = parser.parse_args(argv)
    provider = embeddings.configured(get_settings())
    if provider is None:
        sys.stderr.write("error: no embedding provider is available (EMBEDDING_PROVIDER=none, or it failed to load)\n")
        return 1
    with session_scope() as session:
        if args.command == "backfill":
            done = semantic.backfill(session, provider, limit=args.limit)
            sys.stdout.write(f"embedded {done} chunks with {provider.model}\n")
        else:
            embedded, chunks = semantic.coverage(session, provider)
            sys.stdout.write(f"{embedded}/{chunks} chunks embedded with {provider.model}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
