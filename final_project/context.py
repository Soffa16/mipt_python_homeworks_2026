from __future__ import annotations

from enum import StrEnum

Message = dict[str, str]


class MessageField(StrEnum):
    ROLE = 'role'
    CONTENT = 'content'


class MessageRole(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


def _is_system(message: Message) -> bool:
    return message[MessageField.ROLE] == MessageRole.SYSTEM


def _system_messages(messages: list[Message]) -> list[Message]:
    return [message for message in messages if _is_system(message)]


def _non_system_messages(messages: list[Message]) -> list[Message]:
    return [message for message in messages if not _is_system(message)]


def _trim_non_system_messages(messages: list[Message], limit: int) -> list[Message]:
    while len(messages) > limit:
        messages = messages[2:]
    return messages


def _trim_last_non_system_message(
    history: list[Message],
    message_index: int,
    excess: int,
) -> list[Message]:
    message = history[message_index]
    history[message_index] = {
        MessageField.ROLE: message[MessageField.ROLE],
        MessageField.CONTENT: message[MessageField.CONTENT][excess:],
    }
    return history


def trim_context(
    history: list[Message],
    limit_messages: int | None,
    limit_chars: int | None,
) -> list[Message]:
    result = list(history)
    if limit_messages is not None:
        result = _trim_by_message_limit(result, limit_messages)
    if limit_chars is not None:
        result = _trim_by_char_limit(result, limit_chars)
    return result


def _trim_by_message_limit(history: list[Message], limit: int) -> list[Message]:
    system = _system_messages(history)
    non_system = _non_system_messages(history)
    # limit — количество пар (user + assistant), поэтому умножаем на 2
    max_messages = limit * 2
    return system + _trim_non_system_messages(non_system, max_messages)


def _get_non_system_indices(messages: list[Message]) -> list[int]:
    return [index for index, message in enumerate(messages) if not _is_system(message)]


def _trim_by_char_limit(history: list[Message], limit: int) -> list[Message]:
    result = list(history)

    while True:
        total = sum(len(m[MessageField.CONTENT]) for m in result)
        if total <= limit:
            break

        non_system_indices = _get_non_system_indices(result)
        if not non_system_indices:
            break

        oldest_idx = non_system_indices[0]

        if len(non_system_indices) == 1:
            excess = total - limit
            return _trim_last_non_system_message(result, oldest_idx, excess)

        result.pop(oldest_idx)

    return result
