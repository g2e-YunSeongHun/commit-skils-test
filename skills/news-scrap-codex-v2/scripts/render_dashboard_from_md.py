#!/usr/bin/env python3
"""Render the weekly HTML dashboard from news_briefing.md."""

from __future__ import annotations

import sys
from pathlib import Path

from briefing_md import parse_briefing_markdown
from render_dashboard import (
    build_article_list,
    collect_articles,
    esc,
    get_text,
    normalize_news_output_path,
    render_template,
    resolve_template_path,
)


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: python render_dashboard_from_md.py <news_briefing.md> <output_html_path> [template_path]"
        )
        sys.exit(1)

    briefing_path = Path(sys.argv[1]).resolve()
    output_path = normalize_news_output_path(Path(sys.argv[2]).resolve())
    template_path = resolve_template_path(sys.argv[3:])

    parsed = parse_briefing_markdown(briefing_path)
    verified = parsed["verified"]
    template = template_path.read_text(encoding="utf-8")

    domestic_articles, overseas_articles = collect_articles(verified)
    replacements = {
        "{{page_title}}": "의료 AI 주간 브리핑",
        "{{period}}": f'{esc(get_text(verified, "시작일", "start_date"))} ~ {esc(get_text(verified, "종료일", "end_date"))}',
        "{{generated_date}}": esc(get_text(verified, "생성일", "generated_date")),
        "{{total_count}}": str(len(domestic_articles) + len(overseas_articles)),
        "{{domestic_count}}": str(len(domestic_articles)),
        "{{overseas_count}}": str(len(overseas_articles)),
        "{{domestic_articles}}": build_article_list(domestic_articles, "국내기사"),
        "{{overseas_articles}}": build_article_list(overseas_articles, "해외기사"),
    }

    rendered = render_template(template, replacements)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
