#!/usr/bin/env python3
"""Generate a NotebookLM slide deck from the featured article."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


SECTION_MARKERS = {
    "deck_prompt": ("DECK_PROMPT_START", "DECK_PROMPT_END"),
    "slide_1": ("SLIDE_1_REVISION_START", "SLIDE_1_REVISION_END"),
    "slide_2": ("SLIDE_2_REVISION_START", "SLIDE_2_REVISION_END"),
    "slide_3": ("SLIDE_3_REVISION_START", "SLIDE_3_REVISION_END"),
    "slide_4": ("SLIDE_4_REVISION_START", "SLIDE_4_REVISION_END"),
    "slide_5": ("SLIDE_5_REVISION_START", "SLIDE_5_REVISION_END"),
}


class SlideDeckError(RuntimeError):
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
    raise SlideDeckError("json_parse", "명령 출력에서 JSON 객체를 찾지 못했습니다.")


def run_command(command: list[str], *, step: str) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise SlideDeckError(step, detail, command)
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


def get_question(outputs: dict, question_id: str) -> dict | None:
    for item in outputs.get("questions", []):
        if item.get("id") == question_id:
            return item
    return None


def get_articles(payload: dict) -> list[tuple[str, dict]]:
    items_out: list[tuple[str, dict]] = []
    for section_name in ("국내기사", "해외기사", "해외논문", "domestic_articles", "overseas_articles"):
        value = payload.get(section_name)
        if not isinstance(value, list):
            continue
        label = "국내기사" if "국내" in section_name or section_name == "domestic_articles" else "해외기사"
        for item in value:
            if isinstance(item, dict):
                items_out.append((label, item))
    return items_out


def get_text(article: dict, *keys: str) -> str:
    for key in keys:
        value = article.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize(text: str) -> str:
    return "".join(re.findall(r"[0-9A-Za-z가-힣]+", text)).lower()


def token_score(answer: str, title: str, media: str) -> int:
    answer_norm = normalize(answer)
    title_norm = normalize(title)
    score = 0
    if title_norm and title_norm in answer_norm:
        score += 1000 + len(title_norm)
    for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", title):
        token_norm = normalize(token)
        if token_norm and token_norm in answer_norm:
            score += len(token_norm) * 5
    media_norm = normalize(media)
    if media_norm and media_norm in answer_norm:
        score += 20
    return score


def parse_featured_answer(answer: str) -> dict:
    parsed: dict[str, str] = {}
    for line in answer.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip().upper()] = value.strip()
    return {
        "title": parsed.get("TITLE", ""),
        "media": parsed.get("MEDIA", ""),
        "date": parsed.get("DATE", ""),
        "reason": parsed.get("REASON", ""),
    }


def choose_featured_article(verified: dict, outputs: dict) -> dict:
    q6 = get_question(outputs, "Q6")
    q4 = get_question(outputs, "Q4")
    answer = ""
    parsed = {}
    if q6 and isinstance(q6.get("answer"), str):
        answer = q6["answer"]
        parsed = parse_featured_answer(answer)
    elif q4 and isinstance(q4.get("answer"), str):
        answer = q4["answer"]

    best_score = -1
    best_article: dict | None = None
    for section, article in get_articles(verified):
        title = get_text(article, "제목", "title")
        media = get_text(article, "기관/매체", "매체", "media")
        score = 0
        if parsed.get("title"):
            score += token_score(parsed["title"], title, media) * 2
        if answer:
            score += token_score(answer, title, media)
        if score > best_score:
            best_score = score
            best_article = {
                "title": title,
                "media": media,
                "date": get_text(article, "날짜", "date"),
                "section": section,
                "related_org": get_text(article, "관련기관", "related_org", "organization"),
                "link": get_text(article, "링크", "link", "url"),
                "reason": parsed.get("reason") or (q4.get("answer", "") if q4 else ""),
            }

    if not best_article:
        raise SlideDeckError("featured_article", "대표 기사를 선택할 수 없습니다.")

    best_source_id = ""
    for source in outputs.get("sources", []):
        if normalize(str(source.get("article_title", ""))) == normalize(best_article["title"]):
            best_source_id = str(source.get("source_id", "")).strip()
            break
    best_article["source_id"] = best_source_id
    return best_article


def read_prompt_section(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    start, end = SECTION_MARKERS[name]
    pattern = rf"<!--{start}-->\s*(.*?)\s*<!--{end}-->"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise SlideDeckError("prompt_parse", f"프롬프트 섹션을 찾지 못했습니다: {name}")
    return match.group(1).strip()


def fill_template(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def safe_slug(value: str) -> str:
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", value)
    slug = "_".join(tokens).strip("_")
    return slug or "slide_deck"


def generate_slide_deck(notebook_id: str, prompt: str, source_id: str) -> dict:
    command = [
        "notebooklm",
        "generate",
        "slide-deck",
        prompt,
        "-n",
        notebook_id,
        "--format",
        "detailed",
        "--length",
        "default",
        "--language",
        "ko",
        "--json",
    ]
    if source_id:
        command.extend(["-s", source_id])
    data = run_command(command, step="slide_generate")
    artifact_id = data.get("artifact_id") or data.get("task_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise SlideDeckError("slide_generate", "slide-deck artifact id를 찾지 못했습니다.", command)
    return {"artifact_id": artifact_id, "status": data.get("status", "pending")}


def revise_slide(notebook_id: str, artifact_id: str, slide_index: int, prompt: str) -> dict:
    command = [
        "notebooklm",
        "generate",
        "revise-slide",
        prompt,
        "-n",
        notebook_id,
        "-a",
        artifact_id,
        "--slide",
        str(slide_index),
        "--json",
    ]
    data = run_command(command, step="slide_revise")
    next_id = data.get("artifact_id") or data.get("task_id") or artifact_id
    return {
        "artifact_id": next_id,
        "status": data.get("status", "pending"),
        "slide_index": slide_index,
    }


def wait_for_artifact(notebook_id: str, artifact_id: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    command = ["notebooklm", "artifact", "list", "-n", notebook_id, "--type", "slide-deck", "--json"]
    last_status = "unknown"
    while time.time() < deadline:
        data = run_command(command, step="artifact_list")
        artifacts = data.get("artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []
        for artifact in artifacts:
            if str(artifact.get("id", "")).strip() != artifact_id:
                continue
            status = str(artifact.get("status", "")).strip().lower()
            last_status = status or "unknown"
            if status == "completed":
                return {"artifact_id": artifact_id, "status": "completed"}
            if status in {"failed", "error"}:
                raise SlideDeckError("artifact_wait", f"artifact 실패: {artifact_id}", command)
        time.sleep(10)
    raise SlideDeckError("artifact_wait", f"artifact 대기 시간 초과: {artifact_id} ({last_status})", command)


def download_slide_deck(notebook_id: str, artifact_id: str, output_path: Path, file_format: str) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)
    output_path.with_suffix(output_path.suffix + ".tmp").unlink(missing_ok=True)
    command = [
        "notebooklm",
        "download",
        "slide-deck",
        str(output_path),
        "-n",
        notebook_id,
        "-a",
        artifact_id,
        "--format",
        file_format,
        "--json",
        "--force",
    ]
    data = run_command(command, step=f"download_{file_format}")
    # NotebookLM CLI can report an error object even after the target file is
    # successfully written on Windows, so prefer the filesystem as ground truth.
    if output_path.exists():
        return str(output_path)
    result_path = data.get("output_path")
    if isinstance(result_path, str) and result_path:
        return result_path
    if data.get("status") == "downloaded" and output_path.exists():
        return str(output_path)
    raise SlideDeckError(f"download_{file_format}", f"{file_format} 다운로드 경로를 찾지 못했습니다.", command)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooklm_outputs_json")
    parser.add_argument("verified_json")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--artifact-id", default="")
    parser.add_argument("--skip-revisions", action="store_true")
    args = parser.parse_args()

    outputs_path = Path(args.notebooklm_outputs_json).resolve()
    verified_path = Path(args.verified_json).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else outputs_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = (
        Path(args.prompt_file).resolve()
        if args.prompt_file
        else Path(__file__).resolve().parent.parent / "references" / "slide_prompt.md"
    )

    notebook_id = ""
    try:
        outputs = load_json(outputs_path)
        verified = load_json(verified_path)
        notebook = outputs.get("notebook", {})
        notebook_id = str(notebook.get("id", "")).strip()
        if not notebook_id:
            raise SlideDeckError("inputs", "notebooklm_outputs.json 에 notebook.id 가 없습니다.")

        featured = choose_featured_article(verified, outputs)
        featured_path = output_dir / "featured_article.json"
        featured_path.write_text(json.dumps(featured, ensure_ascii=False, indent=2), encoding="utf-8")

        values = {
            "WEEK_ID": str(outputs.get("week_id", verified_path.stem.replace("verified_articles_", ""))),
            "FEATURED_TITLE": featured.get("title", ""),
            "FEATURED_MEDIA": featured.get("media", ""),
            "FEATURED_DATE": featured.get("date", ""),
            "FEATURED_ORG": featured.get("related_org", "") or "기사에 등장한 핵심 기관 또는 기술 주체",
            "FEATURED_LINK": featured.get("link", ""),
            "SOURCE_SCOPE": "대표 기사 source 중심" if featured.get("source_id") else "전체 NotebookLM source 참고",
        }

        if args.artifact_id:
            generation = {"artifact_id": args.artifact_id, "status": "resumed"}
            generation_wait = wait_for_artifact(notebook_id, args.artifact_id, 1200)
            artifact_id = generation_wait["artifact_id"]
            generation["status"] = generation_wait["status"]
        else:
            deck_prompt = fill_template(read_prompt_section(prompt_path, "deck_prompt"), values)
            generation = generate_slide_deck(notebook_id, deck_prompt, featured.get("source_id", ""))
            generation_wait = wait_for_artifact(notebook_id, generation["artifact_id"], 1200)
            artifact_id = generation_wait["artifact_id"]
            generation["status"] = generation_wait["status"]

        revisions: list[dict] = []
        if not args.skip_revisions:
            for slide_number, section_name in enumerate(("slide_1", "slide_2", "slide_3", "slide_4", "slide_5")):
                prompt = fill_template(read_prompt_section(prompt_path, section_name), values)
                result = revise_slide(notebook_id, artifact_id, slide_number, prompt)
                wait_result = wait_for_artifact(notebook_id, result["artifact_id"], 900)
                artifact_id = wait_result["artifact_id"]
                revisions.append({"slide_index": slide_number, "status": wait_result["status"]})

        slug = safe_slug(values["WEEK_ID"])
        pdf_path = output_dir / f"news_slide_{slug}.pdf"
        pptx_path = output_dir / f"news_slide_{slug}.pptx"
        downloads = {
            "pdf": download_slide_deck(notebook_id, artifact_id, pdf_path, "pdf"),
            "pptx": download_slide_deck(notebook_id, artifact_id, pptx_path, "pptx"),
        }

        artifact_payload = {
            "notebook_id": notebook_id,
            "artifact_id": artifact_id,
            "featured_article": featured,
            "generation": generation,
            "revisions": revisions,
            "downloads": downloads,
        }
        artifact_path = output_dir / "slide_deck_artifact.json"
        artifact_path.write_text(
            json.dumps(artifact_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"DONE:{artifact_path}")
    except SlideDeckError as error:
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
