from pathlib import Path

from lembrai.onboarding import ask_profile, save_profile


def test_profile_is_built_from_answered_questions():
    answers = iter(["Gabriel", "Dev, acordo cedo", "", "Lembrar de tudo"])
    content = ask_profile(ask=lambda _prompt: next(answers))
    assert content is not None
    assert "## Nome\nGabriel" in content
    assert "## Sobre\nDev, acordo cedo" in content
    assert "## Preferências" not in content
    assert content.endswith("\n")


def test_profile_is_none_when_every_answer_is_blank():
    assert ask_profile(ask=lambda _prompt: "   ") is None


def test_save_profile_creates_the_parent_directory(tmp_path: Path):
    target = tmp_path / "data" / "profile.md"
    save_profile("## Nome\nG\n", path=target)
    assert target.read_text(encoding="utf-8") == "## Nome\nG\n"
