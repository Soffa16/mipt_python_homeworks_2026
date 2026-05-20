from __future__ import annotations

from context import (
    MessageField,
    MessageRole,
    _trim_by_char_limit,
    _trim_by_message_limit,
    trim_context,
)

Message = dict[str, str]

_CC = 'cc'


def _u(content: str) -> Message:
    return {MessageField.ROLE: MessageRole.USER, MessageField.CONTENT: content}


def _a(content: str) -> Message:
    return {MessageField.ROLE: MessageRole.ASSISTANT, MessageField.CONTENT: content}


def _s(content: str) -> Message:
    return {MessageField.ROLE: MessageRole.SYSTEM, MessageField.CONTENT: content}


class TestMessageLimit:
    def test_within_limit_unchanged(self) -> None:
        history = [_u('hi'), _a('hello')]
        assert _trim_by_message_limit(history, 2) == history

    def test_excess_removes_oldest_pair(self) -> None:
        p1 = [_u('1'), _a('r1')]
        p2 = [_u('2'), _a('r2')]
        p3 = [_u('3'), _a('r3')]
        history = p1 + p2 + p3
        result = _trim_by_message_limit(history, 2)
        assert result == p2 + p3

    def test_system_prompt_preserved(self) -> None:
        sys_msg = _s('You are a helpful assistant.')
        p1 = [_u('1'), _a('r1')]
        p2 = [_u('2'), _a('r2')]
        p3 = [_u('3'), _a('r3')]
        history = [sys_msg] + p1 + p2 + p3
        result = _trim_by_message_limit(history, 2)
        assert result[0] == sys_msg
        assert len([m for m in result if m[MessageField.ROLE] != MessageRole.SYSTEM]) == 4

    def test_exact_limit_unchanged(self) -> None:
        p1 = [_u('a'), _a('b')]
        p2 = [_u('c'), _a('d')]
        history = p1 + p2
        result = _trim_by_message_limit(history, 4)
        assert result == history

    def test_limit_one_pair(self) -> None:
        old_pair = [_u('old1'), _a('oldr1')]
        new_pair = [_u('new'), _a('newr')]
        history = old_pair + new_pair
        result = _trim_by_message_limit(history, 1)
        assert result == new_pair


class TestCharLimit:
    def test_within_limit_unchanged(self) -> None:
        history = [_u('hello'), _a('world')]
        result = _trim_by_char_limit(history, 100)
        assert result == history

    def test_removes_oldest_non_system(self) -> None:
        first = [_u('aaaa'), _a('bbbb')]
        second = [_u(_CC), _a('dd')]
        history = first + second
        result = _trim_by_char_limit(history, 8)
        assert _u('aaaa') not in result
        assert _u(_CC) in result

    def test_system_prompt_never_removed(self) -> None:
        sys_msg = _s(MessageRole.SYSTEM)
        history = [sys_msg, _u('short')]
        result = _trim_by_char_limit(history, 100)
        assert sys_msg in result

    def test_truncates_last_message_from_left(self) -> None:
        history = [_u('abcdefghij')]
        result = _trim_by_char_limit(history, 5)
        assert result[0][MessageField.CONTENT] == 'fghij'

    def test_truncates_with_system_present(self) -> None:
        sys_msg = _s('sys')
        history = [sys_msg, _u('abcdefghij')]
        result = _trim_by_char_limit(history, 7)
        assert result[0] == sys_msg
        assert len(result[1][MessageField.CONTENT]) == 4
        assert result[1][MessageField.CONTENT] == 'ghij'

    def test_empty_history_unchanged(self) -> None:
        assert _trim_by_char_limit([], 10) == []


class TestBothLimits:
    def test_message_limit_applied_first(self) -> None:
        sys_msg = _s('sys')
        history = [
            sys_msg,
            _u('aaa'),
            _a('bbb'),
            _u(_CC),
            _a('dd'),
            _u('e'),
            _a('f'),
        ]
        result = trim_context(history, limit_messages=2, limit_chars=1000)
        non_sys = [m for m in result if m[MessageField.ROLE] != MessageRole.SYSTEM]
        assert len(non_sys) == 4
        assert sys_msg in result

    def test_both_limits_applied(self) -> None:
        first = [_u('aaaa'), _a('bbbb')]
        second = [_u(_CC), _a('dd')]
        history = first + second
        result = trim_context(history, limit_messages=4, limit_chars=8)
        total = sum(len(m[MessageField.CONTENT]) for m in result)
        assert total <= 8

    def test_no_limits_unchanged(self) -> None:
        history = [_u('hello'), _a('world')]
        assert trim_context(history, None, None) == history
