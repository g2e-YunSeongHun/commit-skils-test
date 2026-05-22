#!/usr/bin/env python3
"""Create a NotebookLM note, upload slide-deck sources, and save session metadata."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


NOTEBOOKLM_AUTO_LOGIN_TIMEOUT_SECONDS = int(os.getenv("NOTEBOOKLM_AUTO_LOGIN_TIMEOUT", "300"))
NOTEBOOKLM_AUTO_LOGIN_DISABLED_VALUES = {"0", "false", "no", "off"}


class GateError(RuntimeError):
    def __init__(self, step: str, detail: str, command: list[str] | None = None):
        super().__init__(detail)
        self.step = step
        self.detail = detail
        self.command = command or []


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def parse_first_json(text: str) -> dict:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise GateError("json_parse", "명령 출력에서 JSON 객체를 찾지 못했습니다.")


def run_command(command: list[str], *, step: str) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise GateError(step, detail, command)
    return parse_first_json(result.stdout.strip())


def write_failure(
    output_dir: Path,
    *,
    step: str,
    detail: str,
    notebook_id: str = "",
    command: list[str] | None = None,
) -> None:
    payload = {
        "step": step,
        "detail": detail,
        "notebook_id": notebook_id,
        "command": command or [],
    }
    path = output_dir / "notebooklm_failure.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _auth_failures(data: dict) -> list[str]:
    checks = data.get("checks", {})
    if not isinstance(checks, dict):
        return []
    required = ("storage_exists", "json_valid", "cookies_present", "sid_cookie", "token_fetch")
    return [name for name in required if checks.get(name) is False]


def _auto_login_enabled() -> bool:
    value = os.getenv("NEWS_SCRAP_NOTEBOOKLM_AUTO_LOGIN", "").strip().lower()
    return value not in NOTEBOOKLM_AUTO_LOGIN_DISABLED_VALUES


def _browser_login(storage_path: Path, timeout_seconds: int) -> None:
    if os.environ.get("NOTEBOOKLM_AUTH_JSON"):
        raise GateError(
            "auth_login",
            "NOTEBOOKLM_AUTH_JSON 환경변수가 설정되어 있어 브라우저 기반 자동 로그인 복구를 사용할 수 없습니다.",
        )

    try:
        from notebooklm.cli.session import (
            GOOGLE_ACCOUNTS_URL,
            NOTEBOOKLM_HOST,
            NOTEBOOKLM_URL,
            _ensure_chromium_installed,
            _windows_playwright_event_loop,
        )
        from notebooklm.paths import get_browser_profile_dir
        from playwright.sync_api import sync_playwright
    except Exception as error:
        raise GateError("auth_login", f"NotebookLM 자동 로그인 준비 실패: {error}") from error

    storage_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    browser_profile = get_browser_profile_dir()
    browser_profile.mkdir(parents=True, exist_ok=True, mode=0o700)

    _ensure_chromium_installed()
    deadline = time.monotonic() + timeout_seconds

    try:
        with _windows_playwright_event_loop(), sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(browser_profile),
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--password-store=basic",
                ],
                ignore_default_args=["--enable-automation"],
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(NOTEBOOKLM_URL, wait_until="load")
                while time.monotonic() < deadline:
                    current_url = page.url
                    cookies = context.cookies()
                    has_google_sid = any(
                        cookie.get("name") in {"SID", "__Secure-1PSID", "__Secure-3PSID"}
                        for cookie in cookies
                    )
                    if NOTEBOOKLM_HOST in current_url and has_google_sid:
                        page.goto(GOOGLE_ACCOUNTS_URL, wait_until="load")
                        page.goto(NOTEBOOKLM_URL, wait_until="load")
                        context.storage_state(path=str(storage_path))
                        storage_path.chmod(0o600)
                        return
                    time.sleep(3)
                raise GateError(
                    "auth_login",
                    f"NotebookLM 자동 로그인 대기 시간 초과: {timeout_seconds}초 안에 NotebookLM 홈으로 진입하지 못했습니다.",
                )
            finally:
                context.close()
    except GateError:
        raise
    except Exception as error:
        raise GateError("auth_login", f"NotebookLM 자동 로그인 실패: {error}") from error


def auth_check() -> None:
    first_error: GateError | None = None
    storage_path = Path(os.getenv("NOTEBOOKLM_STORAGE", "")).expanduser() if os.getenv("NOTEBOOKLM_STORAGE") else None
    try:
        data = run_command(["notebooklm", "auth", "check", "--json"], step="auth_check")
        failed = _auth_failures(data)
        if not failed:
            return
        first_error = GateError("auth_check", f"NotebookLM 인증 체크 실패: {', '.join(failed)}")
    except GateError as error:
        data = {}
        first_error = error

    if not _auto_login_enabled():
        raise first_error

    details = data.get("details", {})
    if storage_path is None:
        storage_value = details.get("storage_path") if isinstance(details, dict) else ""
        storage_path = Path(storage_value).expanduser() if storage_value else Path.home() / ".notebooklm" / "storage_state.json"

    _browser_login(storage_path, NOTEBOOKLM_AUTO_LOGIN_TIMEOUT_SECONDS)
    retry = run_command(["notebooklm", "auth", "check", "--json"], step="auth_check")
    retry_failed = _auth_failures(retry)
    if retry_failed:
        raise GateError(
            "auth_check",
            f"NotebookLM 자동 로그인 후에도 인증 체크 실패: {', '.join(retry_failed)}",
        )


def create_notebook(title: str) -> dict:
    data = run_command(["notebooklm", "create", title, "--json"], step="create")
    notebook = data.get("notebook") if isinstance(data.get("notebook"), dict) else data
    if not isinstance(notebook, dict) or not notebook.get("id"):
        raise GateError("create", "notebooklm create 응답에서 notebook id를 찾지 못했습니다.")
    return {"id": notebook["id"], "title": notebook.get("title", title)}


def add_source(notebook_id: str, source: dict) -> dict:
    command = [
        "notebooklm",
        "source",
        "add",
        source["file_path"],
        "-n",
        notebook_id,
        "--title",
        source["title"],
        "--json",
    ]
    data = run_command(command, step="source_add")
    source_payload = data.get("source") if isinstance(data.get("source"), dict) else data
    source_id = source_payload.get("source_id") or source_payload.get("id")
    if not isinstance(source_id, str) or not source_id:
        raise GateError("source_add", f"소스 업로드 응답이 비정상적입니다: {source['title']}", command)
    return {"id": source_id, "title": source_payload.get("title", source["title"])}


def wait_source(notebook_id: str, source_id: str) -> None:
    command = ["notebooklm", "source", "wait", source_id, "-n", notebook_id, "--timeout", "180", "--json"]
    data = run_command(command, step="source_wait")
    if data.get("status") != "ready":
        raise GateError("source_wait", f"소스 준비 실패: {source_id}", command)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_json")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    manifest_path = Path(args.manifest_json).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else manifest_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    notebook_id = ""
    try:
        auth_check()
        manifest = load_json(manifest_path)
        notebook = create_notebook(manifest["notebook_title"])
        notebook_id = notebook["id"]

        sources_out: list[dict] = []
        for source in manifest.get("sources", []):
            added = add_source(notebook_id, source)
            wait_source(notebook_id, added["id"])
            source_record = {
                "source_id": added["id"],
                "title": source["title"],
                "file_path": source["file_path"],
                "section": source["section"],
                "article_title": source["article_title"],
                "date": source["date"],
                "link": source["link"],
            }
            if source.get("source_kind"):
                source_record["source_kind"] = source["source_kind"]
            sources_out.append(source_record)

        payload = {
            "week_id": manifest["week_id"],
            "notebook": {"id": notebook["id"], "title": notebook["title"]},
            "sources": sources_out,
        }
        output_path = output_dir / "notebooklm_session.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"DONE:{output_path}")
    except GateError as error:
        write_failure(
            output_dir,
            step=error.step,
            detail=error.detail,
            notebook_id=notebook_id,
            command=error.command,
        )
        print(f"FAILED:{error.step}:{error.detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:  # pragma: no cover
        write_failure(output_dir, step="unknown", detail=str(error), notebook_id=notebook_id)
        print(f"FAILED:unknown:{error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
