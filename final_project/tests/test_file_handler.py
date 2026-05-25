from __future__ import annotations

from pathlib import Path

import pytest

from file_handler import MAX_FILE_SIZE, chunk_by_length, chunk_by_paragraph, read_file


class TestReadFile:
    def test_reads_text(self, tmp_path: Path) -> None:
        f = tmp_path / 'hello.txt'
        f.write_text('Hello, world!')
        assert read_file(str(f)) == 'Hello, world!'

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            read_file('/no/such/file.txt')

    def test_too_large_raises(self, tmp_path: Path) -> None:
        f = tmp_path / 'big.bin'
        f.write_bytes(b'x' * (MAX_FILE_SIZE + 1))
        with pytest.raises(ValueError, match='too large'):
            read_file(str(f))

    def test_exactly_max_size_ok(self, tmp_path: Path) -> None:
        f = tmp_path / 'edge.txt'
        f.write_bytes(b'a' * MAX_FILE_SIZE)
        content = read_file(str(f))
        assert len(content) == MAX_FILE_SIZE


class TestChunkByParagraph:
    def test_single_paragraph(self) -> None:
        chunks = chunk_by_paragraph('Hello world')
        assert chunks == ['Hello world']

    def test_two_paragraphs(self) -> None:
        text = 'Para one.\n\nPara two.'
        chunks = chunk_by_paragraph(text)
        assert len(chunks) == 2
        assert chunks[0] == 'Para one.'
        assert chunks[1] == 'Para two.'

    def test_strips_blank_paragraphs(self) -> None:
        text = 'A\n\n\n\nB'
        chunks = chunk_by_paragraph(text)
        assert chunks == ['A', 'B']

    def test_group_size_two(self) -> None:
        text = 'A\n\nB\n\nC\n\nD'
        chunks = chunk_by_paragraph(text, group_size=2)
        assert len(chunks) == 2
        assert 'A' in chunks[0] and 'B' in chunks[0]
        assert 'C' in chunks[1] and 'D' in chunks[1]

    def test_group_size_larger_than_count(self) -> None:
        text = 'A\n\nB'
        chunks = chunk_by_paragraph(text, group_size=5)
        assert len(chunks) == 1
        assert 'A' in chunks[0]

    def test_empty_text_returns_empty_list(self) -> None:
        assert chunk_by_paragraph('') == []
        assert chunk_by_paragraph('   \n\n  ') == []


class TestChunkByLength:
    def test_even_split(self) -> None:
        chunks = chunk_by_length('abcdef', 2)
        assert chunks == ['ab', 'cd', 'ef']

    def test_remainder_chunk(self) -> None:
        chunks = chunk_by_length('abcde', 2)
        assert chunks == ['ab', 'cd', 'e']

    def test_length_larger_than_text(self) -> None:
        chunks = chunk_by_length('hello', 100)
        assert chunks == ['hello']

    def test_empty_text(self) -> None:
        assert chunk_by_length('', 10) == []

    def test_length_one(self) -> None:
        chunks = chunk_by_length('abc', 1)
        assert chunks == ['a', 'b', 'c']
