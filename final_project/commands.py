from __future__ import annotations

import re
from enum import StrEnum

import display
from file_handler import read_file

_FILE_REF_PATTERN = re.compile(r'@::(.+?)::')


class Command(StrEnum):
    QUIT = r'\q'
    RESET = '/reset'
    FILE_CHUNK = '/file_chunk'


def _read_file_ref(path: str) -> str | None:
    try:
        return read_file(path)
    except FileNotFoundError as error:
        display.print_error(str(error))
        return None
    except (ValueError, OSError) as error:
        display.print_error(str(error))
        return ''


def is_quit(text: str) -> bool:
    return text == Command.QUIT


def is_reset(text: str) -> bool:
    return text == Command.RESET


def is_file_chunk(text: str) -> bool:
    return text.startswith(Command.FILE_CHUNK)


def expand_file_refs(message: str) -> str | None:
    matches = _FILE_REF_PATTERN.findall(message)
    for path in matches:
        content = _read_file_ref(path)
        if content is None:
            return None
        if content == '':
            message = message.replace(f'@::{path}::', '', 1)
            continue
        message = message.replace(f'@::{path}::', content, 1)
    return message


def parse_file_chunk_options(cmd: str) -> tuple[int | None, int | None, bool]:
    auto_yes = '-y' in cmd

    paragraph_group: int | None = None
    m = re.search(r'paragraph=(\d+)', cmd)
    if m:
        paragraph_group = _parse_positive_int(m.group(1), 'paragraph')

    char_len: int | None = None
    m = re.search(r'len=(\d+)', cmd)
    if m:
        char_len = _parse_positive_int(m.group(1), 'len')

    return paragraph_group, char_len, auto_yes


def _parse_positive_int(value: str, name: str) -> int | None:
    result = int(value)
    if result <= 0:
        print(f'Error: {name} must be a positive integer, got: {value!r}')
        return None
    return result
