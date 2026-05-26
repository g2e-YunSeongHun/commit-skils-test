#!/usr/bin/env python3
"""Apply Pencil template_bindings directly to a weekly .pen file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BIND_PREFIX = "bind."

OPTIONAL_GROUPS = [
    ["bind.s1.point1"],
    ["bind.s1.point2"],
    ["bind.s1.point3"],
    ["bind.s2.step1"],
    ["bind.s2.step2"],
    ["bind.s2.step3"],
    ["bind.s2.capability1.title", "bind.s2.capability1.detail"],
    ["bind.s2.capability2.title", "bind.s2.capability2.detail"],
    ["bind.s2.capability3.title", "bind.s2.capability3.detail"],
    ["bind.s2.capability4.title", "bind.s2.capability4.detail"],
    ["bind.s3.founded"],
    ["bind.s3.headquarters"],
    ["bind.s3.scale"],
    ["bind.s3.focus"],
    ["bind.s3.offering1.title", "bind.s3.offering1.detail"],
    ["bind.s3.offering2.title", "bind.s3.offering2.detail"],
    ["bind.s3.offering3.title", "bind.s3.offering3.detail"],
    ["bind.s4.fact1.label", "bind.s4.fact1.value", "bind.s4.fact1.detail"],
    ["bind.s4.fact2.label", "bind.s4.fact2.value", "bind.s4.fact2.detail"],
    ["bind.s4.fact3.label", "bind.s4.fact3.value", "bind.s4.fact3.detail"],
    ["bind.s4.meaning1"],
    ["bind.s4.meaning2"],
    ["bind.s4.meaning3"],
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def walk_nodes(node: Any, parent: dict[str, Any] | None = None):
    if isinstance(node, dict):
        yield node, parent
        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                yield from walk_nodes(child, node)
    elif isinstance(node, list):
        for child in node:
            yield from walk_nodes(child, parent)


def text_value(value: Any) -> str:
    return str(value or "").strip()


def node_label(node: dict[str, Any] | None) -> str:
    if not node:
        return ""
    return str(node.get("name") or node.get("id") or "")


def nearest_hide_target(parent: dict[str, Any] | None) -> dict[str, Any] | None:
    if not parent:
        return None
    if parent.get("type") in {"frame", "group"}:
        return parent
    return None


def load_bindings(spec_path: Path) -> dict[str, str]:
    spec = read_json(spec_path)
    if not isinstance(spec, dict):
        raise SystemExit(f"Pencil spec JSON 형식이 올바르지 않습니다: {spec_path}")

    template = spec.get("template") or {}
    mode = template.get("mode")
    if mode and mode != "update_named_bindings":
        raise SystemExit(f"지원하지 않는 Pencil template.mode입니다: {mode}")

    bindings = spec.get("template_bindings")
    if not isinstance(bindings, dict):
        raise SystemExit(f"template_bindings를 찾지 못했습니다: {spec_path}")
    return {str(key): text_value(value) for key, value in bindings.items()}


def apply_bindings(
    pen: dict[str, Any],
    bindings: dict[str, str],
    *,
    strict: bool,
    keep_empty_cards: bool,
) -> dict[str, Any]:
    bind_nodes: dict[str, dict[str, Any]] = {}
    parent_by_name: dict[str, dict[str, Any] | None] = {}

    for node, parent in walk_nodes(pen):
        if node.get("type") != "text":
            continue
        name = str(node.get("name") or "")
        if not name.startswith(BIND_PREFIX):
            continue
        bind_nodes[name] = node
        parent_by_name[name] = parent

    missing_template_nodes = sorted(key for key in bindings if key.startswith(BIND_PREFIX) and key not in bind_nodes)
    if missing_template_nodes and strict:
        raise SystemExit("템플릿에서 binding node를 찾지 못했습니다: " + ", ".join(missing_template_nodes))

    updated = 0
    cleared = 0
    for name, node in bind_nodes.items():
        value = bindings.get(name, "")
        node["content"] = value
        if value:
            updated += 1
        else:
            cleared += 1

    hidden_groups = 0
    shown_groups = 0
    if not keep_empty_cards:
        for group in OPTIONAL_GROUPS:
            existing_names = [name for name in group if name in bind_nodes]
            if not existing_names:
                continue
            target = nearest_hide_target(parent_by_name.get(existing_names[0]))
            if not target:
                continue
            has_content = any(bindings.get(name, "").strip() for name in group)
            if has_content:
                if target.get("enabled") is False:
                    shown_groups += 1
                target["enabled"] = True
            else:
                if target.get("enabled") is not False:
                    hidden_groups += 1
                target["enabled"] = False

    unresolved_template_nodes = sorted(name for name in bind_nodes if name not in bindings)
    return {
        "updated_bindings": updated,
        "cleared_bindings": cleared,
        "hidden_groups": hidden_groups,
        "shown_groups": shown_groups,
        "missing_template_nodes": missing_template_nodes,
        "unresolved_template_nodes": unresolved_template_nodes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pen_file")
    parser.add_argument("spec_json")
    parser.add_argument("--output", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--keep-empty-cards", action="store_true")
    args = parser.parse_args()

    pen_path = Path(args.pen_file).resolve()
    spec_path = Path(args.spec_json).resolve()
    output_path = Path(args.output).resolve() if args.output else pen_path

    if not pen_path.exists():
        raise SystemExit(f"Pencil 작업 파일을 찾지 못했습니다: {pen_path}")
    if not spec_path.exists():
        raise SystemExit(f"Pencil spec 파일을 찾지 못했습니다: {spec_path}")

    pen = read_json(pen_path)
    if not isinstance(pen, dict) or not isinstance(pen.get("children"), list):
        raise SystemExit(f"Pencil .pen 파일 형식이 올바르지 않습니다: {pen_path}")

    bindings = load_bindings(spec_path)
    report = apply_bindings(
        pen,
        bindings,
        strict=args.strict,
        keep_empty_cards=args.keep_empty_cards,
    )
    write_json(output_path, pen)

    print(f"DONE:{output_path}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
