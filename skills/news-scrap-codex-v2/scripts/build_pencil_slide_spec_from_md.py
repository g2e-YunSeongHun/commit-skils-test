#!/usr/bin/env python3
"""Build a Pencil MCP slide specification from news_briefing.md."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from briefing_md import parse_briefing_markdown
from build_pencil_slide_spec import build_spec, normalize_week_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("briefing_md")
    parser.add_argument("output_dir")
    parser.add_argument("--week-id", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    briefing_path = Path(args.briefing_md).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = parse_briefing_markdown(briefing_path)
    week_id = (
        normalize_week_id(args.week_id)
        or normalize_week_id(output_dir.name)
        or normalize_week_id(output_dir.parent.name)
        or normalize_week_id(briefing_path.parent.name)
        or normalize_week_id(briefing_path.parent.parent.name)
    )
    if not week_id:
        raise SystemExit("주차 ID를 확인하지 못했습니다. --week-id 또는 주차명이 포함된 output_dir를 사용하세요.")

    spec = build_spec(
        verified=parsed["verified"],
        featured_meta=parsed["featured_meta"],
        research_sections=parsed["research_sections"],
        week_id=week_id,
    )
    spec["generator"] = "news-scrap-codex-v2/scripts/build_pencil_slide_spec_from_md.py"
    spec["source"] = {"briefing_md": str(briefing_path)}

    output_path = Path(args.output).resolve() if args.output else output_dir / "pencil_slide_spec.json"
    output_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
