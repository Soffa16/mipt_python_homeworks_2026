from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from config import _parse_positive_int, _parse_temperature, load_config

_CONFIG_YAML = 'config.yaml'
_API_KEY = 'API_KEY'
_API_HOST_ENV = 'API_HOST'
_MODEL_KEY = 'MODEL'
_LIMIT_MESSAGES = 'limit_messages'


class TestLoadConfigFromYaml:
    def test_valid_full_yaml(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / _CONFIG_YAML
        cfg_file.write_text(
            'api_key: key123\napi_host: http://localhost/v1/\nmodel: gpt-4\n'
            'temperature: 0.5\nlimit_messages: 10\nlimit_chars: 500\n'
            'system_prompt: Be helpful\n'
        )
        config = load_config(str(cfg_file))
        assert config.api_key == 'key123'
        assert config.api_host == 'http://localhost/v1/'
        assert config.model == 'gpt-4'
        assert config.temperature == pytest.approx(0.5)
        assert config.limit_messages == 10
        assert config.limit_chars == 500
        assert config.system_prompt == 'Be helpful'

    def test_minimal_required_only(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / _CONFIG_YAML
        cfg_file.write_text('api_key: k\napi_host: http://h/\nmodel: m\n')
        config = load_config(str(cfg_file))
        assert config.temperature == pytest.approx(0.7)
        assert config.limit_messages is None
        assert config.limit_chars is None
        assert config.system_prompt is None

    def test_missing_yaml_uses_defaults(self, tmp_path: Path) -> None:
        missing = str(tmp_path / 'no_such.yaml')
        with (
            patch.dict(os.environ, {_API_KEY: 'k', _API_HOST_ENV: 'h', _MODEL_KEY: 'm'}),
        ):
            config = load_config(missing)
        assert config.api_key == 'k'

    def test_malformed_yaml_exits(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / 'bad.yaml'
        cfg_file.write_text(': :\n  bad: [unclosed\n')
        with pytest.raises(SystemExit):
            load_config(str(cfg_file))


class TestEnvOverride:
    def test_env_overrides_yaml(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / _CONFIG_YAML
        cfg_file.write_text('api_key: yaml_key\napi_host: http://yaml/\nmodel: yaml_model\n')
        with patch.dict(os.environ, {_API_KEY: 'env_key', _MODEL_KEY: 'env_model'}):
            config = load_config(str(cfg_file))
        assert config.api_key == 'env_key'
        assert config.model == 'env_model'
        assert config.api_host == 'http://yaml/'

    def test_env_temperature_override(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / _CONFIG_YAML
        cfg_file.write_text('api_key: k\napi_host: h\nmodel: m\ntemperature: 0.3\n')
        with patch.dict(os.environ, {'TEMPERATURE': '0.9'}):
            config = load_config(str(cfg_file))
        assert config.temperature == pytest.approx(0.9)


class TestMissingRequired:
    def test_missing_api_key_exits(self, tmp_path: Path) -> None:
        cfg_file = tmp_path / _CONFIG_YAML
        cfg_file.write_text('api_host: h\nmodel: m\n')
        env = {k: '' for k in (_API_KEY, _API_HOST_ENV, _MODEL_KEY)}
        with patch.dict(os.environ, env, clear=False), pytest.raises(SystemExit):
            load_config(str(cfg_file))

    def test_missing_all_required_exits(self, tmp_path: Path) -> None:
        missing = str(tmp_path / 'no.yaml')
        clean = {k: '' for k in (_API_KEY, _API_HOST_ENV, _MODEL_KEY)}
        with patch.dict(os.environ, clean, clear=False), pytest.raises(SystemExit):
            load_config(missing)


class TestParsePositiveInt:
    def test_invalid_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_positive_int('abc', _LIMIT_MESSAGES)

    def test_zero_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_positive_int('0', _LIMIT_MESSAGES)

    def test_negative_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_positive_int('-5', 'limit_chars')

    def test_valid(self) -> None:
        assert _parse_positive_int('42', _LIMIT_MESSAGES) == 42

    def test_none_returns_none(self) -> None:
        assert _parse_positive_int(None, _LIMIT_MESSAGES) is None


class TestParseTemperature:
    def test_out_of_range_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_temperature('1.5')

    def test_negative_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_temperature('-0.1')

    def test_valid_boundary(self) -> None:
        assert _parse_temperature('0.0') == pytest.approx(0)
        assert _parse_temperature('1.0') == pytest.approx(1)

    def test_none_returns_default(self) -> None:
        assert _parse_temperature(None) == pytest.approx(0.7)

    def test_invalid_string_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_temperature('hot')
