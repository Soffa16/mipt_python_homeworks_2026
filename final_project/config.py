from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    api_host: str
    api_key: str
    model: str
    limit_messages: int | None = None
    limit_chars: int | None = None
    temperature: float = 0.7
    system_prompt: str | None = None


def _load_yaml_data(config_path: str) -> dict[str, object]:
    if not os.path.exists(config_path):
        return {}
    try:
        loaded = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        print(f'Error parsing {config_path}: {e}')
        sys.exit(1)
    except OSError as e:
        print(f'Error reading {config_path}: {e}')
        sys.exit(1)
    return loaded if isinstance(loaded, dict) else {}


def load_config(config_path: str = 'config.yaml') -> Config:
    yaml_data = _load_yaml_data(config_path)

    def get_value(yaml_key: str, env_var: str) -> str | None:
        env_val = os.environ.get(env_var)
        if env_val is not None:
            return env_val
        yaml_val = yaml_data.get(yaml_key)
        if yaml_val is None:
            return None
        return str(yaml_val)

    api_host = get_value('api_host', 'API_HOST')
    api_key = get_value('api_key', 'API_KEY')
    model = get_value('model', 'MODEL')

    required_values = {'api_host': api_host, 'api_key': api_key, 'model': model}
    missing = [name for name, value in required_values.items() if not value]
    if missing:
        print('Error: missing required config parameters:', ', '.join(missing))
        sys.exit(1)

    limit_messages = _parse_positive_int(
        get_value('limit_messages', 'LIMIT_MESSAGES'), 'limit_messages'
    )
    limit_chars = _parse_positive_int(get_value('limit_chars', 'LIMIT_CHARS'), 'limit_chars')
    temperature = _parse_temperature(get_value('temperature', 'TEMPERATURE'))
    system_prompt = get_value('system_prompt', 'SYSTEM_PROMPT')

    return Config(
        api_host=api_host,  # type: ignore[arg-type]
        api_key=api_key,  # type: ignore[arg-type]
        model=model,  # type: ignore[arg-type]
        limit_messages=limit_messages,
        limit_chars=limit_chars,
        temperature=temperature,
        system_prompt=system_prompt,
    )


def _parse_positive_int(value: str | None, name: str) -> int | None:
    if value is None:
        return None
    try:
        result = int(value)
    except ValueError:
        print(f'Error: {name} must be a positive integer, got: {value!r}')
        sys.exit(1)
    if result <= 0:
        print(f'Error: {name} must be a positive integer, got: {value!r}')
        sys.exit(1)
    return result


def _parse_temperature(value: str | None) -> float:
    if value is None:
        return 0.7
    try:
        result = float(value)
    except ValueError:
        print(f'Error: temperature must be a float between 0 and 1, got: {value!r}')
        sys.exit(1)
    if result < 0 or result > 1:
        print(f'Error: temperature must be a float between 0 and 1, got: {value!r}')
        sys.exit(1)
    return result
