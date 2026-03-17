"""뉴스 기사 원문 + 발행일 일괄 추출 스크립트.

Usage:
    echo '["https://example.com/article1", "https://example.com/article2"]' | python extract.py
    또는
    echo -e "https://example.com/article1\nhttps://example.com/article2" | python extract.py

Output (stdout):
    JSON 배열 — 각 항목에 url, text, date, title, success 포함

폴백 체인: trafilatura → Playwright (headless browser)
"""

import io
import json
import sys

import trafilatura

# Windows 콘솔 UTF-8 출력 보장
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")


def _fetch_with_playwright(url: str) -> str | None:
    """trafilatura 실패 시 Playwright headless 브라우저로 HTML 다운로드."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            page = ctx.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            ctx.close()
            browser.close()
            if len(html) > 500:
                return html
    except Exception:
        pass
    return None


def _extract_from_html(html: str, result: dict) -> dict:
    """다운로드된 HTML에서 본문 + 메타데이터를 추출."""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=False,
        favor_recall=True,
    )
    metadata = trafilatura.extract_metadata(html)

    if text:
        result["text"] = text
        result["success"] = True

    if metadata:
        result["title"] = metadata.title or ""
        result["date"] = metadata.date

    # text 없어도 date만 있으면 부분 성공
    if not text and metadata and metadata.date:
        result["success"] = True

    return result


def extract_article(url: str) -> dict:
    result = {"url": url, "text": "", "date": None, "title": "", "success": False}
    try:
        # 1차: trafilatura 기본 fetch
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)
            if result["success"]:
                return result

        # 2차: Playwright headless 브라우저
        downloaded = _fetch_with_playwright(url)
        if downloaded:
            result = _extract_from_html(downloaded, result)

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("[]")
        return

    # JSON 배열 또는 줄바꿈 구분 URL 지원
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
