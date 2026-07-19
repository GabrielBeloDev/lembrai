from datetime import datetime
from pathlib import Path

from lembrai.reminders import Reminder, ReminderStore, select_due

NOW = datetime(2026, 7, 19, 12, 0, 0)


def reminder(rid: str, due: str, delivered: bool = False) -> Reminder:
    return Reminder(
        id=rid,
        message=f"msg {rid}",
        due=due,
        created_at="2026-07-19T00:00:00",
        delivered=delivered,
    )


def test_select_due_ignores_future_reminders():
    assert select_due([reminder("a", "2026-07-20T09:00:00")], NOW) == []


def test_select_due_includes_the_boundary():
    at_now = [reminder("a", "2026-07-19T12:00:00")]
    assert select_due(at_now, NOW) == at_now


def test_select_due_excludes_already_delivered():
    delivered = [reminder("a", "2026-07-18T09:00:00", delivered=True)]
    assert select_due(delivered, NOW) == []


def test_select_due_sorts_by_due():
    later = reminder("b", "2026-07-19T11:00:00")
    earlier = reminder("a", "2026-07-19T08:00:00")
    assert select_due([later, earlier], NOW) == [earlier, later]


def test_store_add_persists_and_reads_back(tmp_path: Path):
    path = tmp_path / "reminders.json"
    ReminderStore(path).add("levar exames", datetime(2026, 7, 25, 14, 0))
    due = ReminderStore(path).deliver_due(datetime(2026, 7, 26))
    assert len(due) == 1
    assert due[0].message == "levar exames"


def test_deliver_due_marks_delivered_and_is_idempotent(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    store.add("beber água", datetime(2026, 7, 19, 8, 0))
    first = store.deliver_due(NOW)
    second = store.deliver_due(NOW)
    assert len(first) == 1
    assert second == []


def test_deliver_due_leaves_future_reminders_pending(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    store.add("futuro", datetime(2026, 8, 1, 9, 0))
    assert store.deliver_due(NOW) == []


def test_deliver_due_marks_only_the_due_ones(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    store.add("agora", datetime(2026, 7, 19, 8, 0))
    store.add("depois", datetime(2026, 7, 20, 9, 0))
    assert [r.message for r in store.deliver_due(NOW)] == ["agora"]
    assert [r.message for r in store.deliver_due(datetime(2026, 7, 21))] == ["depois"]
