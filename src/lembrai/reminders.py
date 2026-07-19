import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path

REMINDERS_PATH = Path("data/reminders.json")


@dataclass(frozen=True)
class Reminder:
    id: str
    message: str
    due: str
    created_at: str
    delivered: bool = False


def select_due(reminders: list[Reminder], now: datetime) -> list[Reminder]:
    pending = [
        reminder
        for reminder in reminders
        if not reminder.delivered and datetime.fromisoformat(reminder.due) <= now
    ]
    return sorted(pending, key=lambda reminder: reminder.due)


class ReminderStore:
    def __init__(self, reminders_path: Path = REMINDERS_PATH):
        self._path = reminders_path

    def _load(self) -> list[Reminder]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [Reminder(**item) for item in raw]

    def all(self) -> list[Reminder]:
        return self._load()

    def _save(self, reminders: list[Reminder]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([asdict(r) for r in reminders], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    def add(self, message: str, due: datetime) -> Reminder:
        created = datetime.now()
        reminder = Reminder(
            id=created.strftime("%Y%m%d-%H%M%S-%f"),
            message=message,
            due=due.isoformat(timespec="seconds"),
            created_at=created.isoformat(timespec="seconds"),
        )
        reminders = self._load()
        reminders.append(reminder)
        self._save(reminders)
        return reminder

    def deliver_due(self, now: datetime) -> list[Reminder]:
        reminders = self._load()
        due = select_due(reminders, now)
        if not due:
            return []
        delivered_ids = {reminder.id for reminder in due}
        self._save(
            [
                replace(reminder, delivered=True)
                if reminder.id in delivered_ids
                else reminder
                for reminder in reminders
            ]
        )
        return due
