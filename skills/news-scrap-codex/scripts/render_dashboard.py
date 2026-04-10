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
    "연구": "tag-research",
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


def normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in (text or "").splitlines():
        line = strip_citations(raw_line)
        line = strip_markdown(line)
        line = re.sub(r"^\s*[-*•]\s*", "", line)
        line = re.sub(r"^\s*\d+[.)]\s*", "", line)
        line = re.sub(r"^\s*(?:기사|article)\s*\d+\s*[:.]\s*", "", line, flags=re.IGNORECASE)
        line = normalize_whitespace(line)
        if line:
            lines.append(line)
    return lines


def is_summary_lead_in(line: str) -> bool:
    text = normalize_whitespace(line)
    return text.startswith(
        (
            "제공된 소스를 바탕으로",
            "제공된 소스만 근거로",
            "제공해 주신 기사별로",
        )
    ) or "다음과 같습니다" in text


def compose_summary_item(lines: list[str]) -> dict[str, str]:
    if not lines:
        return {"title": "", "body": ""}
    heading = lines[0]
    body_lines = [line for line in lines[1:] if not is_summary_lead_in(line)]
    if not body_lines:
        return {"title": heading, "body": ""}
    body = first_sentences(" ".join(body_lines), max_sentences=1, max_chars=180)
    return {"title": heading, "body": body}


def extract_items(text: str, max_items: int) -> list[dict[str, str]]:
    seen: set[str] = set()
    items: list[dict[str, str]] = []
    blocks = [block for block in re.split(r"\n\s*\n", text or "") if block.strip()]

    for block in blocks:
        lines = [line for line in normalize_lines(block) if not is_summary_lead_in(line)]
        item = compose_summary_item(lines)
        label = " ".join(part for part in (item["title"], item["body"]) if part).strip()
        if len(label) < 8:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
        if len(items) >= max_items:
            break

    if items:
        return items

    for line in normalize_lines(text):
        if is_summary_lead_in(line) or len(line) < 8:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": line, "body": ""})
        if len(items) >= max_items:
            break
    return items


def score_ai_builder_item(item: dict[str, str]) -> int:
    title = normalize_whitespace(item.get("title", "")).lower()
    body = normalize_whitespace(item.get("body", "")).lower()
    combined = f"{title} {body}"

    developer_keywords = (
        "개발",
        "공개",
        "오픈소스",
        "제공",
        "보유",
        "develop",
        "developer",
        "build",
        "built",
    )
    product_keywords = (
        "모델",
        "플랫폼",
        "솔루션",
        "product",
        "platform",
        "model",
        "solution",
    )
    adopter_keywords = (
        "도입",
        "선정",
        "파트너로",
        "partner로",
        "adopt",
        "adoption",
        "select",
        "selected",
        "evaluation",
        "평가",
        "시뮬레이션",
        "simulation",
    )
    institution_keywords = (
        "대학교",
        "대학",
        "병원",
        "연구진",
        "연구소",
        "연구원",
        "university",
        "hospital",
        "institute",
        "school",
        "lab",
    )
    research_only_keywords = (
        "평가",
        "시뮬레이션",
        "simulation",
        "연구진",
        "연구 결과",
        "비교 분석",
    )

    has_developer_signal = any(keyword in combined for keyword in developer_keywords)
    has_product_signal = any(keyword in combined for keyword in product_keywords)
    has_adopter_signal = any(keyword in combined for keyword in adopter_keywords)
    is_institution_like = any(keyword in title for keyword in institution_keywords)
    is_research_only = any(keyword in combined for keyword in research_only_keywords)

    if has_adopter_signal and not has_developer_signal:
        return -10
    if is_institution_like and is_research_only and not has_developer_signal:
        return -10

    score = 0
    if has_developer_signal:
        score += 4
    if has_product_signal:
        score += 1
    if has_adopter_signal:
        score -= 2
    if is_institution_like:
        score -= 1
        if has_developer_signal:
            score += 2
    return score


def select_ai_builder_items(items: list[dict[str, str]], max_items: int) -> list[dict[str, str]]:
    ranked: list[tuple[int, dict[str, str]]] = []
    for item in items:
        score = score_ai_builder_item(item)
        if score <= 0:
            continue
        ranked.append((score, item))

    ranked.sort(
        key=lambda pair: (
            -pair[0],
            pair[1].get("title", "").lower(),
        )
    )
    return [item for _, item in ranked[:max_items]]


def looks_like_technology_name(text: str) -> bool:
    normalized = normalize_whitespace(text).lower()
    technology_keywords = (
        "ai",
        "assistant",
        "model",
        "platform",
        "solution",
        "system",
        "엔진",
        "모델",
        "플랫폼",
        "솔루션",
        "시스템",
        "기술",
    )
    return any(keyword in normalized for keyword in technology_keywords)


def technology_sentence_score(sentence: str) -> int:
    text = normalize_whitespace(sentence).lower()
    positive_keywords = (
        "ai 기반",
        "모델",
        "플랫폼",
        "시스템",
        "솔루션",
        "도구",
        "문서화",
        "판독",
        "추론",
        "분석",
        "탐지",
        "지원",
        "자동화",
        "기록",
        "진단",
        "triage",
        "workflow",
        "documentation",
        "diagnostic",
        "reasoning",
        "interpretation",
    )
    weak_keywords = (
        "발표",
        "선정",
        "도입",
        "제휴",
        "파트너",
        "파트너십",
        "체결",
    )

    score = sum(2 for keyword in positive_keywords if keyword in text)
    score -= sum(3 for keyword in weak_keywords if keyword in text)
    return score


def choose_technology_sentences(text: str, max_sentences: int = 2) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""

    ranked = sorted(
        enumerate(sentences),
        key=lambda pair: (
            -technology_sentence_score(pair[1]),
            pair[0],
        ),
    )
    chosen_indexes = sorted(index for index, _ in ranked[:max_sentences] if technology_sentence_score(sentences[index]) > 0)
    if not chosen_indexes:
        return first_sentences(text, max_sentences=1, max_chars=220)
    chosen = " ".join(sentences[index] for index in chosen_indexes)
    return first_sentences(chosen, max_sentences=max_sentences, max_chars=220)


def collect_all_articles(verified: dict) -> list[dict]:
    domestic_articles, overseas_articles = collect_articles(verified)
    return domestic_articles + overseas_articles


def match_builder_item_to_article(item: dict[str, str], articles: list[dict]) -> dict | None:
    item_text = normalize_whitespace(" ".join(part for part in (item.get("title", ""), item.get("body", "")) if part))
    item_tokens = set(re.findall(r"[0-9A-Za-z가-힣]{2,}", item_text.lower()))
    best_article: dict | None = None
    best_score = 0

    for article in articles:
        haystack = " ".join(
            [
                get_article_title(article),
                get_article_original_title(article),
                get_text(article, "기관/매체", "매체", "media"),
                get_text(article, "관련기관", "related_org", "organization"),
                get_text(article, "적용분야", "domain"),
                get_text(article, "본문", "body", "content"),
            ]
        )
        haystack_norm = normalize_whitespace(haystack).lower()
        score = 0
        for token in item_tokens:
            if token in haystack_norm:
                score += len(token)
        title_norm = normalize_whitespace(item.get("title", "")).lower()
        if title_norm and title_norm in haystack_norm:
            score += 50
        if score > best_score:
            best_score = score
            best_article = article

    return best_article


def extract_technology_label(article: dict, item: dict[str, str]) -> str:
    item_title = normalize_whitespace(item.get("title", ""))
    if looks_like_technology_name(item_title):
        return item_title

    translated_title = get_article_title(article)
    match = re.search(r"^[^,]+,\s*(.+?)(?:\s+(?:공개|개발|발표|선정|도입|출시).*)?$", translated_title)
    if match:
        candidate = normalize_whitespace(match.group(1))
        candidate = re.sub(r"\s*를\s+AI.+$", "", candidate)
        candidate = re.sub(r"\s*을\s+AI.+$", "", candidate)
        if candidate:
            return candidate

    domain = get_text(article, "적용분야", "domain")
    if domain:
        return domain
    return item_title


def build_company_technology_items(
    items: list[dict[str, str]],
    verified: dict,
    source_lookup: dict[str, str],
    q0_summaries: dict[str, str],
) -> list[dict[str, str]]:
    articles = collect_all_articles(verified)
    enriched: list[dict[str, str]] = []

    for item in items:
        article = match_builder_item_to_article(item, articles)
        if not article:
            enriched.append(item)
            continue

        technology_label = extract_technology_label(article, item)
        entity_label = normalize_whitespace(item.get("title", ""))
        if entity_label and technology_label and normalize_key(entity_label) != normalize_key(technology_label):
            title = f"{entity_label} / {technology_label}"
        else:
            title = technology_label or entity_label

        source_id = get_article_source_id(article, source_lookup)
        summary_text = q0_summaries.get(source_id) or get_text(article, "본문", "body", "content")
        technology_body = choose_technology_sentences(summary_text, max_sentences=2)

        if not technology_body:
            technology_body = normalize_whitespace(item.get("body", "")) or "기술 설명이 없습니다."

        enriched.append(
            {
                "title": title,
                "body": technology_body,
            }
        )

    return enriched


def normalize_key(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", strip_citations(str(text or "")).lower())


def collect_articles(verified: dict) -> tuple[list[dict], list[dict]]:
    domestic = verified.get("국내기사")
    if not isinstance(domestic, list):
        domestic = []

    overseas: list[dict] = []
    for key in ("해외기사", "해외논문"):
        value = verified.get(key)
        if isinstance(value, list):
            overseas.extend(item for item in value if isinstance(item, dict))

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

    source_id = get_article_source_id(article, source_lookup)
    summary = q0_summaries.get(source_id) or first_sentences(
        get_text(article, "본문", "body", "content"),
        max_sentences=4,
        max_chars=700,
    )
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


def build_list_items(items: list[dict[str, str]], empty_message: str) -> str:
    if not items:
        items = [{"title": "", "body": empty_message}]

    rendered_items: list[str] = []
    for item in items:
        title = esc(item.get("title", ""))
        body = esc(item.get("body", ""))
        if title and body:
            rendered_items.append(f"          <li><strong>{title}</strong><br />{body}</li>")
        elif title:
            rendered_items.append(f"          <li>{title}</li>")
        else:
            rendered_items.append(f"          <li>{body}</li>")
    return "\n".join(rendered_items)


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
    q1 = get_question(outputs, "Q1")
    q2 = get_question(outputs, "Q2")
    q3 = get_question(outputs, "Q3")
    q2_items = build_company_technology_items(
        select_ai_builder_items(extract_items(get_text(q2, "answer"), 4), 4),
        verified,
        source_lookup,
        q0_summaries,
    )

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
        "{{summary_trends}}": build_list_items(
            extract_items(get_text(q1, "answer"), 3),
            "주간 동향 요약이 없습니다.",
        ),
        "{{summary_featured_orgs}}": build_list_items(
            q2_items,
            "주요 기업 / 기술 요약이 없습니다.",
        ),
        "{{summary_implications}}": build_list_items(
            extract_items(get_text(q3, "answer"), 3),
            "시사점 요약이 없습니다.",
        ),
    }

    rendered = render_template(template, replacements)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"DONE:{output_path}")


if __name__ == "__main__":
    main()
