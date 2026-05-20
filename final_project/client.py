from __future__ import annotations

from openai import OpenAI

from config import Config

Message = dict[str, str]


def send_message(history: list[Message], config: Config) -> str:
    client = OpenAI(api_key=config.api_key, base_url=config.api_host)
    response = client.chat.completions.create(
        model=config.model,
        messages=history,  # type: ignore[arg-type]
        temperature=config.temperature,
    )
    content = response.choices[0].message.content
    return content or ''
