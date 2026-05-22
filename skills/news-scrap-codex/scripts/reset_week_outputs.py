#!/usr/bin/env python3
"""Remove generated files from a news-scrap-codex run directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


GENERATED_FILES = {
    "search_queries.json",
    "candidates_raw.json",
    "verified_articles.json",
    "notebook_manifest.json",
    "notebooklm_session.json",
    # Legacy artifact from the pre-refactor NotebookLM analysis flow.
    "notebooklm_outputs.json",
    "featured_article.json",
    "selection_report.json",
    "article_summaries.json",
    "featured_research.md",
    "featured_research.json",
    "slide_deck_artifact.json",
    "notebooklm_failure.json",
}

GENERATED_PATTERNS = (
    "verified_articles_*.json",
    "news_*.html",
    "news_slide_*.pdf",
    "news_slide_*.pptx",
    "*.tmp",
)

GENERATED_DIRS = {
    "sources",
}


def collect_targets(run_dir: Path) -> list[Path]:
    targets: list[Path] = []

    for name in sorted(GENERATED_FILES):
        candidate = run_dir / name
        if candidate.exists():
            targets.append(candidate)

    for pattern in GENERATED_PATTERNS:
        targets.extend(sorted(path for path in run_dir.glob(pattern) if path.exists()))

    for name in sorted(GENERATED_DIRS):
        candidate = run_dir / name
        if candidate.exists():
            targets.append(candidate)

    return sorted(set(targets), key=lambda path: str(path).lower())


def remove_target(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete generated news-scrap-codex outputs from one run directory."
    )
    parser.add_argument("run_dir", help="run directory for the target week")
    parser.add_argument("--dry-run", action="store_true", help="print targets without deleting them")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.exists():
        print(f"SKIP: run_dir does not exist: {run_dir}")
        return
    if not run_dir.is_dir():
        raise SystemExit(f"run_dir is not a directory: {run_dir}")

    targets = collect_targets(run_dir)
    action = "WOULD_DELETE" if args.dry_run else "DELETE"
    for target in targets:
        print(f"{action}:{target}")
        if not args.dry_run:
            remove_target(target)
    print(f"DONE:{len(targets)} targets")


if __name__ == "__main__":
    main()
