import json
from pathlib import Path

from lembrai.tools import Toolbox


def make_toolbox(tmp_path: Path) -> Toolbox:
    return Toolbox(
        calendar_path=tmp_path / "calendar.json",
        outbox_dir=tmp_path / "outbox",
    )


def test_create_event_persists_sorted_by_date(tmp_path: Path):
    toolbox = make_toolbox(tmp_path)
    toolbox.create_event("Reunião", "2026-08-01", "10:00")
    toolbox.create_event("Dentista", "2026-07-25", "14:00")
    events = json.loads((tmp_path / "calendar.json").read_text(encoding="utf-8"))
    assert [event["title"] for event in events] == ["Dentista", "Reunião"]


def test_create_event_without_time(tmp_path: Path):
    result = make_toolbox(tmp_path).create_event("Aniversário", "2026-09-10")
    assert result == "Evento criado: Aniversário em 2026-09-10."


def test_list_events_on_an_empty_calendar(tmp_path: Path):
    assert make_toolbox(tmp_path).list_events() == "A agenda está vazia."


def test_list_events_formats_every_event(tmp_path: Path):
    toolbox = make_toolbox(tmp_path)
    toolbox.create_event("Dentista", "2026-07-25", "14:00")
    listing = toolbox.list_events()
    assert "2026-07-25 14:00: Dentista" in listing


def test_send_email_writes_to_the_outbox(tmp_path: Path):
    toolbox = make_toolbox(tmp_path)
    result = toolbox.send_email("a@b.com", "Oi", "Corpo")
    saved = list((tmp_path / "outbox").iterdir())
    assert len(saved) == 1
    content = saved[0].read_text(encoding="utf-8")
    assert "Para: a@b.com" in content
    assert "Assunto: Oi" in content
    assert "caixa de saída local" in result


def test_execute_rejects_unknown_tool(tmp_path: Path):
    result = make_toolbox(tmp_path).execute("delete_everything", {})
    assert "Ferramenta desconhecida" in result


def test_execute_reports_invalid_arguments_back(tmp_path: Path):
    result = make_toolbox(tmp_path).execute("create_event", {"nome": "x"})
    assert "Argumentos inválidos" in result
