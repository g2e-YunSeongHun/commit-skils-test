#!/usr/bin/env python3
"""Normalize a Pencil MCP PDF export into the skill's final output name."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def normalize_week_id(value: str) -> str:
    match = re.search(
        r"(?P<year>\d{2})년?[_\s-]*(?P<month>\d{1,2})월?[_\s-]*(?P<week>\d{1,2})주차",
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
    parser.add_argument("exported_pdf")
    parser.add_argument("output_dir")
    parser.add_argument("--week-id", default="")
    parser.add_argument("--spec-json", default="")
    parser.add_argument("--pen-file", default="")
    parser.add_argument("--slide-count", type=int, default=4)
    parser.add_argument("--work-dir", default="")
    parser.add_argument("--keep-work-dir", action="store_true")
    parser.add_argument("--write-artifact", action="store_true")
    args = parser.parse_args()

    exported_pdf = Path(args.exported_pdf).resolve()
    if not exported_pdf.exists():
        raise SystemExit(f"Pencil PDF export를 찾지 못했습니다: {exported_pdf}")
    if exported_pdf.suffix.lower() != ".pdf":
        raise SystemExit(f"Pencil export는 PDF여야 합니다: {exported_pdf}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    week_id = (
        normalize_week_id(args.week_id)
        or load_spec_week_id(args.spec_json)
        or normalize_week_id(output_dir.name)
        or normalize_week_id(exported_pdf.stem)
    )
    if not week_id:
        raise SystemExit("주차 ID를 확인하지 못했습니다. --week-id 또는 --spec-json을 지정하세요.")

    target_pdf = output_dir / f"news_slide_{week_id}.pdf"
    if exported_pdf != target_pdf:
        if target_pdf.exists():
            target_pdf.unlink()
        shutil.move(str(exported_pdf), str(target_pdf))

    if args.write_artifact:
        artifact = {
            "generator": "pencil_mcp",
            "week_id": week_id,
            "pdf": str(target_pdf),
            "source_export_pdf": str(exported_pdf),
            "spec_json": str(Path(args.spec_json).resolve()) if args.spec_json else "",
            "pen_file": str(Path(args.pen_file).resolve()) if args.pen_file else "",
            "slide_count": args.slide_count,
            "format": "pdf",
        }
        artifact_path = output_dir / "pencil_slide_artifact.json"
        artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.work_dir and not args.keep_work_dir:
        work_dir = Path(args.work_dir).resolve()
        if work_dir.exists():
            expected_parent = output_dir.resolve()
            if work_dir.name != "_work" or work_dir.parent.resolve() != expected_parent:
                raise SystemExit(f"안전하지 않은 작업 디렉터리 정리 요청입니다: {work_dir}")
            shutil.rmtree(work_dir)
    print(f"DONE:{target_pdf}")


if __name__ == "__main__":
    main()
