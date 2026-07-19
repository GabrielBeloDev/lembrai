from pathlib import Path

from lembrai.profile import BASE_PROMPT, build_system_prompt, load_profile


def test_load_profile_returns_none_when_file_is_missing(tmp_path: Path):
    assert load_profile(tmp_path / "profile.md") is None


def test_load_profile_returns_none_when_file_is_empty(tmp_path: Path):
    path = tmp_path / "profile.md"
    path.write_text("   \n", encoding="utf-8")
    assert load_profile(path) is None


def test_load_profile_reads_stripped_content(tmp_path: Path):
    path = tmp_path / "profile.md"
    path.write_text("\nSou o Gabriel, dev.\n", encoding="utf-8")
    assert load_profile(path) == "Sou o Gabriel, dev."


def test_system_prompt_without_profile_is_the_base_prompt():
    assert build_system_prompt(None) == BASE_PROMPT


def test_system_prompt_with_profile_includes_it():
    prompt = build_system_prompt("Gosto de café.")
    assert prompt.startswith(BASE_PROMPT)
    assert "Gosto de café." in prompt
