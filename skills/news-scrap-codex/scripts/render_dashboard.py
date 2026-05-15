#!/usr/bin/env python3
"""Render the weekly HTML dashboard for a news-scrap-codex run."""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPT_DIR.parent / "templates" / "dashboard.html"
TAG_CLASS_MAP = {
    "도입/제휴": "tag-deploy",
    "정책": "tag-policy",
    "기술/제품": "tag-trend",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def esc(value: object) -> str:
    return html.escape(str(value or "").strip())


def get_text(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def get_question(outputs: dict, question_id: str) -> dict:
    for item in outputs.get("questions", []):
        if item.get("id") == question_id:
            return item
    return {}


def strip_citations(text: str) -> str:
    return re.sub(r"\[[0-9,\s]+\]", "", text or "")


def strip_markdown(text: str) -> str:
    cleaned = re.sub(r"[*_`]+", "", text or "")
    cleaned = cleaned.replace("###", "").replace("##", "").replace("#", "")
    return cleaned


def strip_article_label(text: str) -> str:
    cleaned = strip_markdown(text)
    cleaned = re.sub(r"^\s*(?:기사|article)\s*\d+\s*[:.]\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def normalize_whitespace(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    normalized = re.sub(r"\s+([.,!?])", r"\1", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    return normalized


def clean_summary_text(text: str) -> str:
    return normalize_whitespace(strip_article_label(strip_citations(text)))


def split_sentences(text: str) -> list[str]:
    cleaned = clean_summary_text(text)
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def first_sentences(text: str, max_sentences: int = 4, max_chars: int = 700) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "요약 정보가 없습니다."
    snippet = " ".join(sentences[:max_sentences]).strip()
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    return snippet


def normalize_key(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", strip_citations(str(text or "")).lower())


def collect_articles(verified: dict) -> tuple[list[dict], list[dict]]:
    domestic = verified.get("국내기사")
    if not isinstance(domestic, list):
        domestic = []

    overseas = verified.get("해외기사")
    if not isinstance(overseas, list):
        overseas = []

    return domestic, overseas


def get_article_title(article: dict) -> str:
    return (
        get_text(article, "번역제목", "translated_title", "제목", "title")
        or "제목 미상"
    )


def get_article_original_title(article: dict) -> str:
    translated = get_article_title(article)
    original = get_text(article, "원제목", "original_title")
    if original and original != translated:
        return original
    title = get_text(article, "제목", "title")
    if title and title != translated:
        return title
    return ""


def build_output_source_lookup(outputs: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for source in outputs.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_id = get_text(source, "source_id", "id")
        if not source_id:
            continue
        for link_key in ("link", "url"):
            link = get_text(source, link_key)
            if link:
                lookup[f"link:{link.strip()}"] = source_id
        for title_key in ("article_title", "title"):
            title = get_text(source, title_key)
            if title:
                lookup[f"title:{normalize_key(title)}"] = source_id
    return lookup


def parse_q0_blocks(answer: str) -> list[dict[str, str | int]]:
    structured_pattern = re.compile(
        r"(?ms)^\s*ARTICLE_INDEX:\s*(\d+)\s*\nTITLE:\s*(.+?)\s*\nSUMMARY:\s*(.*?)(?=^\s*ARTICLE_INDEX:\s*\d+\s*$|\Z)"
    )
    structured_blocks: list[dict[str, str | int]] = []
    for match in structured_pattern.finditer(answer or ""):
        structured_blocks.append(
            {
                "index": int(match.group(1)),
                "heading": normalize_whitespace(strip_article_label(match.group(2))),
                "body": match.group(3).strip(),
            }
        )
    if structured_blocks:
        return structured_blocks

    pattern = re.compile(
        r"(?ms)^\s*\*{0,2}\s*(?:기사\s*)?(\d+)\s*[:.]\s*(.+?)\s*\*{0,2}\s*\n(.*?)(?=^\s*\*{0,2}\s*(?:기사\s*)?\d+\s*[:.]\s+|\Z)"
    )
    blocks: list[dict[str, str | int]] = []
    for match in pattern.finditer(answer or ""):
        heading = normalize_whitespace(strip_article_label(match.group(2)))
        body = match.group(3).strip()
        blocks.append(
            {
                "index": int(match.group(1)),
                "heading": heading,
                "body": body,
            }
        )
    if blocks:
        return blocks

    fallback_blocks = [
        chunk.strip() for chunk in re.split(r"\n\s*\n", answer or "") if chunk.strip()
    ]
    for index, chunk in enumerate(fallback_blocks, start=1):
        blocks.append({"index": index, "heading": "", "body": chunk})
    return blocks


def build_citation_source_map(question: dict) -> dict[str, str]:
    citation_map: dict[str, str] = {}
    for reference in question.get("references", []):
        if not isinstance(reference, dict):
            continue
        citation_number = reference.get("citation_number")
        source_id = get_text(reference, "source_id")
        if citation_number is None or not source_id:
            continue
        citation_map[str(citation_number)] = source_id
    return citation_map


def choose_source_for_block(
    block: dict[str, str | int],
    citation_map: dict[str, str],
    output_sources: list[dict],
) -> str:
    citations = re.findall(r"\[(\d+)\]", str(block.get("body", "")))
    counted = Counter(citation_map[number] for number in citations if number in citation_map)
    if counted:
        return counted.most_common(1)[0][0]

    ordered_source_map = {
        str(index): get_text(source, "source_id", "id")
        for index, source in enumerate(output_sources, start=1)
        if isinstance(source, dict) and get_text(source, "source_id", "id")
    }
    ordered_counts = Counter(
        ordered_source_map[number] for number in citations if number in ordered_source_map
    )
    if ordered_counts:
        return ordered_counts.most_common(1)[0][0]

    heading_key = normalize_key(str(block.get("heading", "")))
    if not heading_key:
        return ""

    best_source_id = ""
    best_score = 0
    heading_tokens = set(re.findall(r"[0-9a-z가-힣]{2,}", heading_key))
    for source in output_sources:
        if not isinstance(source, dict):
            continue
        source_id = get_text(source, "source_id", "id")
        if not source_id:
            continue
        candidate_title = get_text(source, "article_title", "title")
        candidate_key = normalize_key(candidate_title)
        if not candidate_key:
            continue
        if heading_key in candidate_key or candidate_key in heading_key:
            score = 100
        else:
            candidate_tokens = set(re.findall(r"[0-9a-z가-힣]{2,}", candidate_key))
            score = len(heading_tokens & candidate_tokens)
        if score > best_score:
            best_score = score
            best_source_id = source_id
    return best_source_id


def extract_q0_summary_by_source(outputs: dict) -> dict[str, str]:
    q0 = get_question(outputs, "Q0")
    answer = get_text(q0, "answer")
    if not answer:
        return {}

    citation_map = build_citation_source_map(q0)
    output_sources = outputs.get("sources", [])
    summaries: dict[str, str] = {}

    for block in parse_q0_blocks(answer):
        source_id = choose_source_for_block(block, citation_map, output_sources)
        if not source_id:
            continue
        body = clean_summary_text(str(block.get("body", "")))
        if not body:
            continue
        summaries[source_id] = first_sentences(body, max_sentences=5, max_chars=900)
    return summaries


def get_article_source_id(article: dict, source_lookup: dict[str, str]) -> str:
    link = get_text(article, "링크", "link", "url")
    if link:
        source_id = source_lookup.get(f"link:{link.strip()}")
        if source_id:
            return source_id

    title_candidates = (
        get_text(article, "원제목", "original_title"),
        get_text(article, "제목", "title"),
        get_text(article, "번역제목", "translated_title"),
    )
    for title in title_candidates:
        if not title:
            continue
        source_id = source_lookup.get(f"title:{normalize_key(title)}")
        if source_id:
            return source_id
    return ""


def render_article(article: dict, source_lookup: dict[str, str], q0_summaries: dict[str, str]) -> str:
    title = esc(get_article_title(article))
    original_title = get_article_original_title(article)
    original_block = ""
    if original_title:
        original_block = f'    <div class="source">원제: {esc(original_title)}</div>\n'

    category = get_text(article, "구분", "category") or "동향"
    category_class = TAG_CLASS_MAP.get(category, "tag-trend")
    domain = esc(get_text(article, "적용분야", "domain") or "미분류")
    date = esc(get_text(article, "날짜", "date") or "날짜 미상")
    source = esc(get_text(article, "기관/매체", "매체", "media") or "출처 미상")
    related = esc(get_text(article, "관련기관", "related_org", "organization"))
    source_line = source if not related else f"{source} · {related}"

    summary = first_sentences(get_text(article, "본문", "body", "content"), max_sentences=4, max_chars=700)
    summary = clean_summary_text(summary)

    link = get_text(article, "링크", "link", "url")
    link_block = ""
    if link:
        safe_link = html.escape(link, quote=True)
        link_block = (
            '        <div class="link">\n'
            f'          <a href="{safe_link}" target="_blank" rel="noreferrer">원문 보기 &rarr;</a>\n'
            "        </div>\n"
        )

    return f"""<details class="article">
  <summary>
    <span class="title">{title}</span>
    <span class="meta">
      <span class="tag {category_class}">{esc(category)}</span>
      <span class="tag tag-field">{domain}</span>
      <span class="date">{date}</span>
    </span>
  </summary>
  <div class="article-body">
    <div class="source">{source_line}</div>
{original_block}    <div class="article-summary">{esc(summary)}</div>
{link_block}  </div>
</details>"""


def build_article_list(
    articles: list[dict], source_lookup: dict[str, str], q0_summaries: dict[str, str]
) -> str:
    if not articles:
        return '<div class="empty-notice">수집된 기사가 없습니다.</div>'
    return "\n\n".join(
        render_article(article, source_lookup, q0_summaries) for article in articles
    )


def render_template(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    return rendered


def resolve_template_path(extra_args: list[str]) -> Path:
    for raw_arg in extra_args:
        candidate = Path(raw_arg).resolve()
        if candidate.suffix.lower() in {".html", ".htm"}:
            return candidate
    return DEFAULT_TEMPLATE


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: python render_dashboard.py <verified_json> <notebooklm_outputs_json> <output_html_path> [featured_article_json] [template_path]"
        )
        sys.exit(1)

    verified_path = Path(sys.argv[1]).resolve()
    outputs_path = Path(sys.argv[2]).resolve()
    output_path = Path(sys.argv[3]).resolve()
    template_path = resolve_template_path(sys.argv[4:])

    verified = load_json(verified_path)
    outputs = load_json(outputs_path)
    template = template_path.read_text(encoding="utf-8")

    domestic_articles, overseas_articles = collect_articles(verified)
    source_lookup = build_output_source_lookup(outputs)
    q0_summaries = extract_q0_summary_by_source(outputs)

    replacements = {
        "{{page_title}}": "응급의료 AI 주간 브리핑",
        "{{period}}": f'{esc(get_text(verified, "시작일"))} ~ {esc(get_text(verified, "종료일"))}',
        "{{generated_date}}": esc(get_text(verified, "생성일")),
        "{{total_count}}": str(len(domestic_articles) + len(overseas_articles)),
        "{{domestic_count}}": str(len(domestic_articles)),
        "{{overseas_count}}": str(len(overseas_articles)),
        "{{domestic_articles}}": build_article_list(
            domestic_articles,
            source_lookup,
            q0_summaries,
        ),
        "{{overseas_articles}}": build_article_list(
            overseas_articles,
            source_lookup,
            q0_summaries,
        ),
    }

    rendered = render_template(template, replacements)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
