#!/usr/bin/env python3
"""Run the required NotebookLM gate and save Q0-Q6 outputs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROMPTS = [
    {
        "id": "Q0",
        "note_title_prefix": "Q0_기사별요약",
        "question": "제공된 소스만 근거로 기사별 상세 요약을 작성해줘. 아래 형식을 기사 수만큼 반복하고 다른 서문이나 결론은 쓰지 마. 각 SUMMARY는 4~5문장으로 누가, 무엇을, 왜, 어떻게를 포함하고 추정은 하지 마. 굵게 표시, 불릿, 번호 목록, '기사 1:' 같은 장식 문구는 쓰지 마.\nARTICLE_INDEX: 1\nTITLE: 기사 제목\nSUMMARY: 요약문",
    },
    {
        "id": "Q1",
        "note_title_prefix": "Q1_주간동향",
        "question": "제공된 소스만 근거로 이번 주 응급의료 AI 동향 3가지를 정리해줘. 각 항목은 2문장 이내로 쓰고 중복 표현을 줄여줘.",
    },
    {
        "id": "Q2",
        "note_title_prefix": "Q2_AI개발주체",
        "question": "제공된 소스만 근거로 이번 주 주목할 AI 기술 개발사, 보유 주체, 또는 핵심 제품 주체를 최대 4개만 골라줘. 단순 도입 기관, 사용 병원, 매체, 연구 수행 기관은 제외하고 실제로 AI 기술을 개발했거나 보유하거나 제공하는 주체만 포함해줘. 각 항목은 '주체명 / 기술 또는 제품명 / 해당 기술이 무엇을 하는지'가 드러나게 2문장 이내로 설명해줘.",
    },
    {
        "id": "Q3",
        "note_title_prefix": "Q3_시사점",
        "question": "제공된 소스만 근거로 응급의료 AI 관점의 시사점 3가지를 정리해줘. 홍보 문구 대신 도입 방식, 검증 방식, 운영상 의미에 초점을 맞춰줘.",
    },
    {
        "id": "Q4",
        "note_title_prefix": "Q4_대표기사선정",
        "question": "제공된 소스만 근거로 이번 주 대표 기사 1건과 선정 이유를 설명해줘. 추가 리서치가 필요한 기관이나 기업이 있다면 2~3곳만 덧붙여줘.",
    },
    {
        "id": "Q5",
        "note_title_prefix": "Q5_출력초안",
        "question": "제공된 소스만 근거로 주간 브리핑 핵심 요약과 발표용 핵심 포인트 초안을 작성해줘. 없는 정보는 쓰지 마.",
    },
    {
        "id": "Q6",
        "note_title_prefix": "Q6_대표기사",
        "question": "Q4에서 선정한 대표 기사 1건을 아래 4줄 형식으로만 답해줘.\nTITLE: 기사 제목\nMEDIA: 매체명\nDATE: YYYY-MM-DD 또는 미상\nREASON: 선정 이유",
    },
]


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


def auth_check() -> None:
    data = run_command(["notebooklm", "auth", "check", "--json"], step="auth_check")
    checks = data.get("checks", {})
    if not isinstance(checks, dict):
        return
    required = ("storage_exists", "json_valid", "cookies_present", "sid_cookie", "token_fetch")
    failed = [name for name in required if checks.get(name) is False]
    if failed:
        raise GateError("auth_check", f"NotebookLM 인증 체크 실패: {', '.join(failed)}")


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


def ask_question(notebook_id: str, source_ids: list[str], week_id: str, prompt: dict) -> dict:
    command = ["notebooklm", "ask", "-n", notebook_id]
    for source_id in source_ids:
        command.extend(["-s", source_id])
    command.extend(
        [
            "--json",
            "--save-as-note",
            "--note-title",
            f"{prompt['note_title_prefix']}_{week_id}",
            prompt["question"],
        ]
    )
    data = run_command(command, step="ask")
    answer = data.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise GateError("ask", f"{prompt['id']} 응답이 비어 있습니다.", command)
    return {
        "id": prompt["id"],
        "note_title": f"{prompt['note_title_prefix']}_{week_id}",
        "question": prompt["question"],
        "answer": answer.strip(),
        "references": data.get("references", []),
    }


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
        source_ids: list[str] = []
        for source in manifest.get("sources", []):
            added = add_source(notebook_id, source)
            wait_source(notebook_id, added["id"])
            sources_out.append(
                {
                    "source_id": added["id"],
                    "title": source["title"],
                    "file_path": source["file_path"],
                    "section": source["section"],
                    "article_title": source["article_title"],
                    "date": source["date"],
                    "link": source["link"],
                }
            )
            source_ids.append(added["id"])

        results = [ask_question(notebook_id, source_ids, manifest["week_id"], prompt) for prompt in PROMPTS]

        payload = {
            "week_id": manifest["week_id"],
            "notebook": {"id": notebook["id"], "title": notebook["title"]},
            "sources": sources_out,
            "questions": results,
        }
        output_path = output_dir / "notebooklm_outputs.json"
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
