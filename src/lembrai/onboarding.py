from collections.abc import Callable
from pathlib import Path

from lembrai.profile import PROFILE_PATH

QUESTIONS = [
    ("Nome", "Como você se chama?"),
    ("Sobre", "Fale um pouco sobre você (trabalho, rotina):"),
    ("Preferências", "O que você gosta (e não gosta)?"),
    ("Objetivos", "No que o lembrai pode te ajudar no dia a dia?"),
]


def ask_profile(ask: Callable[[str], str] = input) -> str | None:
    sections: list[str] = []
    for title, question in QUESTIONS:
        answer = ask(f"{question} ").strip()
        if answer:
            sections.append(f"## {title}\n{answer}")
    if not sections:
        return None
    return "\n\n".join(sections) + "\n"


def save_profile(content: str, path: Path = PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
