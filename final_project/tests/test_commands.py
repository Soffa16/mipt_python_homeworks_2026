from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from commands import (
    Command,
    expand_file_refs,
    is_file_chunk,
    is_quit,
    is_reset,
    parse_file_chunk_options,
)


class TestCommandDetection:
    def test_quit_exact(self) -> None:
        assert is_quit(Command.QUIT) is True

    def test_quit_not_exact(self) -> None:
        assert is_quit(f'{Command.QUIT} extra') is False
        assert is_quit('') is False

    def test_reset_exact(self) -> None:
        assert is_reset(Command.RESET) is True

    def test_reset_with_extra(self) -> None:
        assert is_reset(f'{Command.RESET} now') is False

    def test_file_chunk_prefix(self) -> None:
        assert is_file_chunk(Command.FILE_CHUNK) is True
        assert is_file_chunk(f'{Command.FILE_CHUNK} len=100') is True
        assert is_file_chunk(f'{Command.FILE_CHUNK}XYZ') is True
        assert is_file_chunk(Command.RESET) is False


class TestExpandFileRefs:
    def test_no_refs_unchanged(self) -> None:
        result = expand_file_refs('Hello world')
        assert result == 'Hello world'

    def test_single_ref_expanded(self, tmp_path: Path) -> None:
        f = tmp_path / 'code.py'
        f.write_text('print("hello")')
        msg = f'Check this: @::{f}::'
        result = expand_file_refs(msg)
        assert result is not None
        assert 'print("hello")' in result
        assert f'@::{f}::' not in result

    def test_multiple_refs_expanded(self, tmp_path: Path) -> None:
        f1 = tmp_path / 'a.txt'
        f2 = tmp_path / 'b.txt'
        f1.write_text('AAA')
        f2.write_text('BBB')
        msg = f'@::{f1}:: and @::{f2}::'
        result = expand_file_refs(msg)
        assert result is not None
        assert 'AAA' in result
        assert 'BBB' in result

    def test_missing_file_returns_none(self) -> None:
        result = expand_file_refs('@::/no/such/file.txt::')
        assert result is None

    def test_large_file_skips_substitution(self, tmp_path: Path) -> None:
        f = tmp_path / 'big.txt'
        f.write_text('x')
        with patch('commands.read_file', side_effect=ValueError('File too large')):
            result = expand_file_refs(f'msg @::{f}::')
        assert result is not None
        assert f'@::{f}::' not in result


class TestParseFileChunkOptions:
    def test_default_no_options(self) -> None:
        pg, cl, ay = parse_file_chunk_options('/file_chunk')
        assert pg is None
        assert cl is None
        assert ay is False

    def test_auto_yes_flag(self) -> None:
        _, _, ay = parse_file_chunk_options('/file_chunk -y')
        assert ay is True

    def test_paragraph_group(self) -> None:
        pg, cl, _ = parse_file_chunk_options('/file_chunk paragraph=3')
        assert pg == 3
        assert cl is None

    def test_char_length(self) -> None:
        pg, cl, _ = parse_file_chunk_options('/file_chunk len=150')
        assert pg is None
        assert cl == 150

    def test_combined_flags(self) -> None:
        pg, cl, ay = parse_file_chunk_options('/file_chunk paragraph=2 -y')
        assert pg == 2
        assert ay is True
