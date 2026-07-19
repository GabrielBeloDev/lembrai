from pathlib import Path

PROFILE_PATH = Path("data/profile.md")

BASE_PROMPT = (
    "Você é o lembrai, um assistente pessoal. "
    "Responda sempre em português, de forma direta, útil e sem enrolação. "
    "Use as ferramentas disponíveis (agenda, e-mail) quando o pedido do usuário "
    "exigir uma ação, não apenas uma resposta."
)


def load_profile(path: Path = PROFILE_PATH) -> str | None:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8").strip()
    return content or None


def build_system_prompt(profile: str | None) -> str:
    if profile is None:
        return BASE_PROMPT
    return f"{BASE_PROMPT}\n\nO que você sabe sobre o usuário:\n{profile}"
