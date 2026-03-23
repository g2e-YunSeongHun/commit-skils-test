#!/usr/bin/env python3
"""
NotebookLM 슬라이드 생성 스크립트.

사용법:
  python slide.py <notebook_id> <output_path> [instructions]

예시:
  python slide.py abc-123 news_output/slide_3주차.pdf "한국어로 작성해줘..."
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from notebooklm import NotebookLMClient
from notebooklm.rpc.types import SlideDeckLength


async def main():
    if len(sys.argv) < 3:
        print("Usage: python slide.py <notebook_id> <output_path> [instructions]")
        sys.exit(1)

    notebook_id = sys.argv[1]
    output_path = sys.argv[2]
    instructions = sys.argv[3] if len(sys.argv) > 3 else None

    async with await NotebookLMClient.from_storage() as client:
        print("슬라이드 생성 요청 중...")
        status = await client.artifacts.generate_slide_deck(
            notebook_id=notebook_id,
            language="ko",
            instructions=instructions,
            slide_length=SlideDeckLength.SHORT,
        )

        print(f"생성 시작: task_id={status.task_id}")
        print("생성 완료 대기 중...")

        result = await client.artifacts.wait_for_completion(
            notebook_id=notebook_id,
            task_id=status.task_id,
            timeout=300.0,
        )

        if result.is_failed:
            print(f"ERROR: {result.error}")
            sys.exit(1)

        print("슬라이드 다운로드 중...")
        path = await client.artifacts.download_slide_deck(
            notebook_id=notebook_id,
            output_path=output_path,
            output_format="pdf",
        )
        print(f"DONE:{path}")


if __name__ == "__main__":
    asyncio.run(main())
