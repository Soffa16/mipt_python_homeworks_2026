from __future__ import annotations

import sys
from itertools import count

import openai

import display
from client import send_message
from commands import (
    expand_file_refs,
    is_file_chunk,
    is_quit,
    is_reset,
    parse_file_chunk_options,
)
from config import Config, load_config
from context import MessageField, MessageRole, trim_context
from file_handler import chunk_by_length, chunk_by_paragraph, read_file

Message = dict[str, str]

def _make_message(role: str, content: str) -> Message:
    return {MessageField.ROLE: role, MessageField.CONTENT: content}


def _build_chunks(paragraph_group: int | None, char_len: int | None, content: str) -> list[str]:
    if char_len is not None:
        return chunk_by_length(content, char_len)
    group = paragraph_group or 1
    return chunk_by_paragraph(content, group)


def _get_chunk_mode_inputs() -> tuple[str, str]:
    file_path = input('>>> Enter file path: ').strip()
    user_prompt = input('>>> What should be done with each chunk? (User Prompt): ').strip()
    return file_path, user_prompt


def _read_chunk_file(file_path: str) -> str | None:
    try:
        return read_file(file_path)
    except (FileNotFoundError, ValueError, OSError) as error:
        display.print_error(str(error))
        return None


def _handle_send_error(error: KeyboardInterrupt | openai.APIError) -> None:
    if isinstance(error, KeyboardInterrupt):
        display.print_info('\n[Request cancelled]')
        return
    if isinstance(error, openai.APIConnectionError):
        display.print_error(f'Connection error: {error}')
        return
    if isinstance(error, openai.AuthenticationError):
        display.print_error(f'Authentication error: {error}')
        return
    if isinstance(error, openai.RateLimitError):
        display.print_error(f'Rate limit exceeded: {error}')
        return
    display.print_error(f'API error: {error}')


def _send_message(messages: list[Message], config: Config) -> tuple[bool, str | None]:
    try:
        return True, send_message(messages, config)
    except (KeyboardInterrupt, openai.APIError) as error:
        _handle_send_error(error)
        return False, None


def _needs_confirmation(auto_yes: bool, index: int, chunks: list[str]) -> bool:
    return index < len(chunks) - 1 and not auto_yes


def _ask_to_continue() -> bool:
    if is_quit(input('>>> ')):
        display.print_goodbye()
        return False
    return True


def _process_chunks(
    chunks: list[str],
    user_prompt: str,
    auto_yes: bool,
    config: Config,
) -> None:
    for index, chunk in enumerate(chunks):
        if not _send_chunk(chunk, user_prompt, config):
            break
        if _needs_confirmation(auto_yes, index, chunks) and not _ask_to_continue():
            break


def _make_user_message(content: str) -> Message:
    return _make_message(MessageRole.USER, content)


def _make_assistant_message(content: str) -> Message:
    return _make_message(MessageRole.ASSISTANT, content)


def _send_chunk(chunk: str, user_prompt: str, config: Config) -> bool:
    message = _make_user_message(f'{chunk}\n\n{user_prompt}')
    success, reply = _send_message([message], config)
    if not success or reply is None:
        return success
    display.print_reply(reply)
    return True


def _run_file_chunk_mode(cmd: str, config: Config) -> None:
    paragraph_group, char_len, auto_yes = parse_file_chunk_options(cmd)

    file_path, user_prompt = _get_chunk_mode_inputs()
    content = _read_chunk_file(file_path)
    if content is None:
        return

    chunks = _build_chunks(paragraph_group, char_len, content)
    if not chunks:
        display.print_info('File has no content to process.')
        return

    _process_chunks(chunks, user_prompt, auto_yes, config)
    display.print_processing_complete()


def _make_initial_history(config: Config) -> list[Message]:
    history: list[Message] = []
    if config.system_prompt:
        history.append(_make_message(MessageRole.SYSTEM, config.system_prompt))
    return history


def _handle_message(user_input: str, history: list[Message], config: Config) -> list[Message]:
    expanded = expand_file_refs(user_input)
    if expanded is None:
        return history
    history.append(_make_user_message(expanded))
    history = trim_context(history, config.limit_messages, config.limit_chars)
    success, reply = _send_message(history, config)
    if not success or reply is None:
        history.pop()
        return history
    history.append(_make_assistant_message(reply))
    display.print_reply(reply)
    return history


def _handle_command(
    user_input: str,
    history: list[Message],
    config: Config,
) -> tuple[list[Message], bool]:
    if is_quit(user_input):
        display.print_goodbye()
        sys.exit(0)
    if is_reset(user_input):
        history = _make_initial_history(config)
        display.clear_screen()
        display.print_reset_confirmation()
        return history, True
    if is_file_chunk(user_input):
        _run_file_chunk_mode(user_input, config)
        return history, True
    return history, False


def chat_loop(config: Config) -> None:
    history = _make_initial_history(config)

    for _ in count():
        user_input = input('>>> ').strip()
        if not user_input:
            continue
        history = _process_user_input(user_input, history, config)


def _process_user_input(
    user_input: str,
    history: list[Message],
    config: Config,
) -> list[Message]:
    history, handled = _handle_command(user_input, history, config)
    if handled:
        return history
    return _handle_message(user_input, history, config)


def main() -> None:
    config = load_config()
    chat_loop(config)


if __name__ == '__main__':
    main()
