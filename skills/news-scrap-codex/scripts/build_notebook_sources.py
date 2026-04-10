#!/usr/bin/env python3
"""Build NotebookLM source files from verified_articles.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_KEYS = {
    "domestic": ("국내기사", "domestic_articles"),
    "overseas": ("해외기사", "해외논문", "overseas_articles"),
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def get_articles(payload: dict, keys: tuple[str, ...]) -> list[dict]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def get_text(article: dict, *keys: str) -> str:
    for key in keys:
        value = article.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def slugify(value: str) -> str:
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", value)
    slug = "_".join(tokens).strip("_")
    return slug[:80] or "article"


def build_source_text(section: str, article: dict) -> str:
    lines = [
        f"섹션: {section}",
        f"제목: {get_text(article, '제목', 'title')}",
        f"매체: {get_text(article, '기관/매체', '매체', 'media')}",
        f"날짜: {get_text(article, '날짜', 'date')}",
        f"링크: {get_text(article, '링크', 'link', 'url')}",
        f"관련기관: {get_text(article, '관련기관', 'related_org', 'organization')}",
        f"적용분야: {get_text(article, '적용분야', 'domain')}",
        f"구분: {get_text(article, '구분', 'category')}",
        "",
        "본문:",
        get_text(article, "본문", "body", "content"),
    ]
    return "\n".join(lines).strip() + "\n"


def build_manifest(payload: dict, output_dir: Path, week_id: str, notebook_title: str) -> dict:
    source_dir = output_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    sources: list[dict] = []
    index = 1
    for section, aliases in (("국내기사", ARTICLE_KEYS["domestic"]), ("해외기사", ARTICLE_KEYS["overseas"])):
        for article in get_articles(payload, aliases):
            body = get_text(article, "본문", "body", "content")
            if not body:
                continue
            title = get_text(article, "제목", "title") or f"article_{index}"
            file_name = f"{index:02d}_{slugify(title)}.txt"
            file_path = source_dir / file_name
            file_path.write_text(build_source_text(section, article), encoding="utf-8")
            sources.append(
                {
                    "title": file_path.stem,
                    "file_path": str(file_path.resolve()),
                    "section": section,
                    "article_title": title,
                    "date": get_text(article, "날짜", "date"),
                    "link": get_text(article, "링크", "link", "url"),
                }
            )
            index += 1

    if not sources:
        raise SystemExit("본문이 포함된 기사 소스가 없어 NotebookLM manifest를 만들 수 없습니다.")

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
