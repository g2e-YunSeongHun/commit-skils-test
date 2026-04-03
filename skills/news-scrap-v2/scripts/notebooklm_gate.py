#!/usr/bin/env python3
"""NotebookLM 필수 게이트 실행기.

manifest를 받아 새 노트를 만들고, 기사별 소스를 업로드한 뒤 Q0~Q5를 수행한다.
중간 단계가 하나라도 실패하면 failure JSON을 저장하고 즉시 종료한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROMPTS = [
    {
        "id": "Q0",
        "note_title_prefix": "Q0_기사별상세요약",
        "question": "제공된 소스만 근거로 기사별 상세 요약을 작성해줘. 각 기사마다 4~5문장으로 누가, 무엇을, 왜, 어떻게를 포함하고 소스에 없는 내용은 추정하지 마라.",
    },
    {
        "id": "Q1",
        "note_title_prefix": "Q1_핵심동향",
        "question": "제공된 소스만 근거로 이번 주 핵심 동향 3가지를 정리해줘. 각 항목은 2문장 이내로 쓰고 추정하지 마라.",
    },
    {
        "id": "Q2",
        "note_title_prefix": "Q2_주목기관기업",
        "question": "제공된 소스만 근거로 이번 주 주목할 기관 또는 기업을 4곳 이내로 선정하고, 각 기관이 기사에서 어떤 역할을 했는지 2문장 이내로 설명해줘. 추정하지 마라.",
    },
    {
        "id": "Q3",
        "note_title_prefix": "Q3_시사점",
        "question": "제공된 소스만 근거로 응급의료 AI 관점의 시사점 3개를 정리해줘. 제품 홍보가 아니라 도입 방식, 검증 방식, 경쟁 포인트에 초점을 맞추고 추정하지 마라.",
    },
    {
        "id": "Q4",
        "note_title_prefix": "Q4_대표기사선정",
        "question": "제공된 소스만 근거로 이번 주 대표 기사 1건과 선정 이유를 정리해줘. 대표 기사와 직접 연결되는 심층 리서치 대상 기관 또는 기업 2~3곳도 함께 제시하고 추정하지 마라.",
    },
    {
        "id": "Q5",
        "note_title_prefix": "Q5_산출물초안",
        "question": "제공된 소스만 근거로 대시보드용 주간 요약 초안, 슬라이드용 기사 요약 초안, 슬라이드용 시사점 초안을 작성해줘. 소스에 없는 정보는 넣지 마라.",
    },
]


class GateError(RuntimeError):
    """NotebookLM 게이트 실패."""

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
        if char not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError("stdout에서 JSON 객체를 찾지 못했습니다.")


def run_command(command: list[str], *, step: str) -> str:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise GateError(step, detail, command)
    return result.stdout.strip()


def write_failure(output_dir: Path, *, step: str, detail: str, notebook_id: str = "", command: list[str] | None = None) -> None:
    payload = {
        "step": step,
        "detail": detail,
        "notebook_id": notebook_id,
        "command": command or [],
    }
    failure_path = output_dir / "notebooklm_failure.json"
    failure_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_notebook(title: str) -> dict:
    raw = run_command(["notebooklm", "create", title, "--json"], step="create")
    data = parse_first_json(raw)
    notebook = data.get("notebook")
    if not isinstance(notebook, dict) or not notebook.get("id"):
        raise GateError("create", "notebooklm create 응답에 notebook.id가 없습니다.")
    return notebook


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
    raw = run_command(command, step="source_add")
    data = parse_first_json(raw)
    added = data.get("source")
    if not isinstance(added, dict) or not added.get("id"):
        raise GateError("source_add", f"소스 업로드 응답이 비정상입니다: {source['title']}", command)
    return added


def wait_source(notebook_id: str, source_id: str) -> dict:
    command = [
        "notebooklm",
        "source",
        "wait",
        source_id,
        "-n",
        notebook_id,
        "--timeout",
        "180",
        "--json",
    ]
    raw = run_command(command, step="source_wait")
    data = parse_first_json(raw)
    if data.get("status") != "ready":
        raise GateError("source_wait", f"소스 준비 실패: {source_id}", command)
    return data


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
    raw = run_command(command, step="ask")
    data = parse_first_json(raw)
    if not isinstance(data.get("answer"), str) or not data["answer"].strip():
        raise GateError("ask", f"{prompt['id']} 응답이 비어 있습니다.", command)
    return {
        "id": prompt["id"],
        "note_title": f"{prompt['note_title_prefix']}_{week_id}",
        "question": prompt["question"],
        "answer": data["answer"].strip(),
        "references": data.get("references", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_json")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    manifest_path = Path(args.manifest_json).resolve()
    manifest = load_json(manifest_path)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else manifest_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    notebook_id = ""
    try:
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
            "notebook": {"id": notebook_id, "title": notebook["title"]},
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
    except Exception as error:  # pragma: no cover - defensive
        write_failure(output_dir, step="unknown", detail=str(error), notebook_id=notebook_id)
        print(f"FAILED:unknown:{error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
