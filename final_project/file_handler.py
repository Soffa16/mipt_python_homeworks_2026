from __future__ import annotations

import os

MAX_FILE_SIZE = 5 * 1024 * 1024


def read_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f'File not found: {path}')
    size = os.path.getsize(path)
    if size > MAX_FILE_SIZE:
        raise ValueError(f'File too large ({size} bytes, max 5 MB): {path}')
    with open(path, encoding='utf-8') as f:
        return f.read()


def chunk_by_paragraph(text: str, group_size: int = 1) -> list[str]:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if group_size == 1:
        return paragraphs
    chunks = []
    for i in range(0, len(paragraphs), group_size):
        chunks.append('\n\n'.join(paragraphs[i : i + group_size]))
    return chunks


def chunk_by_length(text: str, length: int) -> list[str]:
    chunks = []
    for i in range(0, len(text), length):
        chunks.append(text[i : i + length])
    return chunks
