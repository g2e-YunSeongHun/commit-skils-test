#!/usr/bin/env python3
"""Copy the Pencil slide template into a run directory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR.parent / "templates" / "news_slide_template.pen"


def normalize_week_id(value: str) -> str:
    match = re.search(
        r"(?P<year>\d{2})년[_\s-]*(?P<month>\d{1,2})월[_\s-]*(?P<week>\d{1,2})주차",
        str(value or ""),
    )
    if not match:
        return ""
    return f"{match.group('year')}년_{int(match.group('month'))}월_{int(match.group('week'))}주차"


def load_spec_week_id(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value).resolve()
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        return normalize_week_id(str(payload.get("week_id", "")))
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--spec-json", default="")
    parser.add_argument("--week-id", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        raise SystemExit(f"Pencil 템플릿 파일을 찾지 못했습니다: {template_path}")

    week_id = (
        normalize_week_id(args.week_id)
        or load_spec_week_id(args.spec_json)
        or normalize_week_id(run_dir.name)
        or normalize_week_id(run_dir.parent.name)
    )
    if not week_id:
        raise SystemExit("주차 ID를 확인하지 못했습니다. --week-id 또는 --spec-json을 지정하세요.")

    output_path = run_dir / f"news_slide_{week_id}.pen"
    if output_path.exists() and not args.force:
        raise SystemExit(f"이미 Pencil 작업 파일이 있습니다. 덮어쓰려면 --force를 사용하세요: {output_path}")

    shutil.copy2(template_path, output_path)
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
