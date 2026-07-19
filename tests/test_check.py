from datetime import datetime
from pathlib import Path

from lembrai.check import due_messages
from lembrai.reminders import ReminderStore


def test_due_messages_formats_and_delivers_once(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    store.add("beber água", datetime(2026, 7, 19, 8, 0))
    now = datetime(2026, 7, 19, 12, 0)
    assert due_messages(store, now) == ["⏰ Lembrete: beber água"]
    assert due_messages(store, now) == []


def test_due_messages_empty_when_nothing_due(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    assert due_messages(store, datetime(2026, 7, 19, 12, 0)) == []
