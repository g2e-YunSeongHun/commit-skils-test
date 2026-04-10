"""뉴스 기사 원문 + 발행일 일괄 추출 스크립트.

Usage:
    echo '["https://example.com/article1", "https://example.com/article2"]' | python extract.py
    또는
    echo -e "https://example.com/article1\nhttps://example.com/article2" | python extract.py

Output (stdout):
    JSON 배열 — 각 항목에 url, text, date, title, success 포함

폴백 체인: trafilatura -> Playwright (headless browser)
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
from datetime import datetime

import trafilatura

# Windows 콘솔 UTF-8 출력 보장
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

MIN_MEANINGFUL_CHARS = 100
MIN_MEANINGFUL_TOKENS = 15

HTML_DATE_PATTERNS = (
    r'article:published_time"\s+content="([^"]+)',
    r'itemprop="datePublished"\s+content="([^"]+)',
    r'name="pubdate"\s+content="([^"]+)',
    r'"datePublished"\s*:\s*"([^"]+)',
)

TEXT_DATE_PATTERNS = (
    r"(?:발행날짜|기사입력|입력|등록일|등록일자|작성일|Published)\s*[:：]?\s*([12]\d{3}[./-]\d{2}[./-]\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?)",
    r"(?:업데이트|수정)\s*[:：]?\s*([12]\d{3}[./-]\d{2}[./-]\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?)",
)

DROP_EXACT_LINES = {
    "로그인",
    "댓글",
    "댓글운영규칙",
    "더보기",
    "최신순",
    "추천순",
    "가",
    "-",
}

DROP_CONTAINS = (
    "가입 시 등록한 정보를 입력해주세요.",
    "로그인을 하시면",
    "개인정보 보호를 위한 비밀번호 변경안내",
    "주기적인 비밀번호 변경으로 개인정보를 지켜주세요.",
    "안전한 개인정보 보호를 위해",
    "30일간 보이지 않기",
    "아이디 앞 네자리 표기",
    "이메일 무단수집 거부",
)

STOP_MARKERS = (
    "댓글",
    "댓글운영규칙",
    "이메일 무단수집 거부",
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def has_meaningful_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    if len(normalized) < MIN_MEANINGFUL_CHARS:
        return False
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", normalized)
    return len(tokens) >= MIN_MEANINGFUL_TOKENS


def normalize_date(raw: str | None) -> str | None:
    if not raw:
        return None
    match = re.search(r"([12]\d{3})[./-]([01]\d)[./-]([0-3]\d)", raw)
    if not match:
        return None
    year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def first_date_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.IGNORECASE)
        if not match:
            continue
        normalized = normalize_date(match.group(1))
        if normalized:
            return normalized
    return None


def choose_best_date(
    html: str,
    raw_text: str,
    cleaned_text: str,
    metadata_date: str | None,
) -> str | None:
    explicit_html_date = first_date_match(html, HTML_DATE_PATTERNS)
    if explicit_html_date:
        return explicit_html_date

    labeled_html_date = first_date_match(html, TEXT_DATE_PATTERNS)
    if labeled_html_date:
        return labeled_html_date

    explicit_text_date = first_date_match(raw_text, TEXT_DATE_PATTERNS)
    if explicit_text_date:
        return explicit_text_date

    cleaned_text_date = first_date_match(cleaned_text, TEXT_DATE_PATTERNS)
    if cleaned_text_date:
        return cleaned_text_date

    normalized_metadata_date = normalize_date(metadata_date)
    if normalized_metadata_date:
        return normalized_metadata_date

    return normalize_date(raw_text)


def clean_extracted_text(text: str) -> str:
    cleaned_lines: list[str] = []
    for raw_line in (text or "").splitlines():
        line = normalize_whitespace(raw_line)
        if not line:
            continue
        if any(line.startswith(marker) for marker in STOP_MARKERS):
            break
        if line in DROP_EXACT_LINES:
            continue
        if any(fragment in line for fragment in DROP_CONTAINS):
            continue
        if not cleaned_lines and line.startswith("- "):
            continue
        if any(line.startswith(prefix) for prefix in ("발행날짜:", "입력:", "업데이트:", "등록일:", "등록일자:")):
            continue
        if re.match(r"^-\s+.+\d{4}[./-]\d{2}[./-]\d{2}", line):
            continue
        if cleaned_lines and line == cleaned_lines[-1]:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _use_headless_browser() -> bool:
    """기본은 headless, 디버깅 시에만 headed 브라우저 허용."""
    return os.getenv("NEWS_SCRAP_HEADED", "").strip().lower() not in {"1", "true", "yes"}


def _fetch_with_playwright(url: str) -> str | None:
    """trafilatura 실패 시 Playwright headless 브라우저로 HTML 다운로드."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=_use_headless_browser())
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            context.close()
            browser.close()
            if len(html) > 500:
                return html
    except Exception:
        pass
    return None


def _extract_from_html(html: str, result: dict) -> dict:
    """다운로드된 HTML에서 본문 + 메타데이터를 추출."""
    raw_text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=False,
        favor_recall=True,
    )
    metadata = trafilatura.extract_metadata(html)
    cleaned_text = clean_extracted_text(raw_text or "")

    if cleaned_text:
        result["text"] = cleaned_text
        result["success"] = has_meaningful_text(cleaned_text)

    if metadata:
        result["title"] = metadata.title or ""
        result["date"] = choose_best_date(html, raw_text or "", cleaned_text, metadata.date)
    else:
        result["date"] = choose_best_date(html, raw_text or "", cleaned_text, result.get("date"))

    return result


def extract_article(url: str) -> dict:
    result = {"url": url, "text": "", "date": None, "title": "", "success": False}
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)
            if result.get("success") and result.get("date"):
                return result

        downloaded = _fetch_with_playwright(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)
    except Exception as error:
        result["error"] = str(error)

    return result


def main() -> None:
    raw = sys.stdin.read().lstrip("\ufeff").strip()
    if not raw:
        print("[]")
        return

    try:
        urls = json.loads(raw)
        if isinstance(urls, str):
            urls = [urls]
    except json.JSONDecodeError:
        urls = [line.strip() for line in raw.splitlines() if line.strip()]

    results = [extract_article(url) for url in urls]
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
