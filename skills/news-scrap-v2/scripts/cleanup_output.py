#!/usr/bin/env python3
"""news_output 폴더 정리 스크립트."""

from __future__ import annotations

import re
import sys
from pathlib import Path


DELETE_PATTERNS = [
    re.compile(r"^q\d+_result\.txt$"),
    re.compile(r"^slide_answer\d*\.txt$"),
    re.compile(r"^slide_data.*\.json$"),
    re.compile(r"^source_text_.*\.txt$"),
    re.compile(r"^parsed_.*\.json$"),
    re.compile(r"^nlm_.*\.json$"),
    re.compile(r"^해외_raw\.json$"),
]


def should_delete(path: Path) -> bool:
    return any(pattern.match(path.name) for pattern in DELETE_PATTERNS)


def extract_version(path: Path) -> int | None:
    match = re.search(r"_v(\d+)(?=\.)", path.stem)
    return int(match.group(1)) if match else None


def safe_unlink(path: Path) -> bool:
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def main() -> None:
    output_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd() / "news_output"
    if not output_dir.exists():
        print(f"SKIP:{output_dir}")
        return

    deleted = []
    for path in output_dir.iterdir():
        if path.is_file() and should_delete(path):
            if safe_unlink(path):
                deleted.append(path.name)

    # 같은 주차의 슬라이드/HTML은 가장 높은 버전만 유지
    for prefix in ("slide_", "news_"):
        groups: dict[str, list[Path]] = {}
        for path in output_dir.glob(f"{prefix}*"):
            if not path.is_file():
                continue
            base = re.sub(r"_v\d+(?=\.)", "", path.stem)
            groups.setdefault(base, []).append(path)
        for _, items in groups.items():
            versioned = [(item, extract_version(item)) for item in items]
            versioned = [(item, version) for item, version in versioned if version is not None]
            if not versioned:
                continue
            keep_version = max(version for _, version in versioned)
            keep_items = {item for item, version in versioned if version == keep_version}
            for item, _ in versioned:
                if item not in keep_items and item.suffix in {".pptx", ".html"} and safe_unlink(item):
                    deleted.append(item.name)

    for name in sorted(set(deleted)):
        print(f"DELETED:{name}")


if __name__ == "__main__":
    main()
