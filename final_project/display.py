from __future__ import annotations

import os
import sys


def print_reply(reply: str) -> None:
    print(reply)


def print_error(msg: str) -> None:
    print(f'[Error] {msg}', file=sys.stderr)


def print_info(msg: str) -> None:
    print(msg)


def clear_screen() -> None:
    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033[2J\033[H', end='', flush=True)


def print_goodbye() -> None:
    print('Goodbye!')


def print_reset_confirmation() -> None:
    print('Chat history cleared.')


def print_processing_complete() -> None:
    print('Processing complete.')
