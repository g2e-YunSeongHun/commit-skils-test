#!/usr/bin/env python3
"""verified_articles.json에서 NotebookLM 업로드용 개별 소스와 manifest 생성."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_KEYS = {
    "domestic": ("국내기사", "domestic_articles"),
    "overseas": ("해외기사", "overseas_articles", "논문", "papers"),
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def get_articles(payload: dict, aliases: tuple[str, ...]) -> list[dict]:
    for alias in aliases:
        value = payload.get(alias)
        if isinstance(value, list):
            return value
    return []


def slugify(value: str) -> str:
    text = re.sub(r"[^\w가-힣]+", "_", value.strip(), flags=re.UNICODE)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:60] or "article"


def build_source_text(section: str, article: dict) -> str:
    lines = [
        f"섹션: {section}",
        f"제목: {article.get('제목', '').strip()}",
        f"매체: {article.get('기관매체', '').strip()}",
        f"발행일: {article.get('날짜', '').strip()}",
        f"링크: {article.get('링크', '').strip()}",
        f"관련기관: {article.get('관련기관', '').strip()}",
        f"활용분야: {article.get('활용분야', '').strip()}",
        f"구분: {article.get('구분', '').strip()}",
        "",
        "원문:",
        str(article.get("원문", "")).strip(),
    ]
    return "\n".join(lines).strip() + "\n"


def build_manifest(payload: dict, output_dir: Path, week_id: str, notebook_title: str) -> dict:
    source_dir = output_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    sources: list[dict] = []
    index = 1
    for section_key, aliases in (("국내기사", ARTICLE_KEYS["domestic"]), ("해외기사", ARTICLE_KEYS["overseas"])):
        for article in get_articles(payload, aliases):
            raw_text = str(article.get("원문", "")).strip()
            if not raw_text:
                continue
            article_title = str(article.get("제목", "")).strip() or f"article_{index}"
            filename = f"{index:02d}_{slugify(article_title)}.txt"
            path = source_dir / filename
            path.write_text(build_source_text(section_key, article), encoding="utf-8")
            sources.append(
                {
                    "title": path.stem,
                    "file_path": str(path.resolve()),
                    "section": section_key,
                    "article_title": article_title,
                    "date": str(article.get("날짜", "")).strip(),
                    "link": str(article.get("링크", "")).strip(),
                }
            )
            index += 1

    if not sources:
        raise SystemExit("원문이 있는 기사 소스가 없어 NotebookLM 소스를 만들 수 없습니다.")

    return {
        "week_id": week_id,
        "notebook_title": notebook_title,
        "source_dir": str(source_dir.resolve()),
        "sources": sources,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("verified_json")
    parser.add_argument("output_dir")
    parser.add_argument("--week-id", default="")
    parser.add_argument("--notebook-title", default="")
    args = parser.parse_args()

    verified_path = Path(args.verified_json).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_json(verified_path)
    week_id = args.week_id.strip() or verified_path.stem.replace("verified_articles_", "")
    notebook_title = args.notebook_title.strip() or f"응급의료_AI_주간브리핑_{week_id}"

    manifest = build_manifest(payload, output_dir, week_id, notebook_title)
    manifest_path = output_dir / "notebook_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE:{manifest_path}")


if __name__ == "__main__":
    main()
