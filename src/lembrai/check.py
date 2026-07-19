from datetime import datetime

from lembrai.reminders import ReminderStore


def due_messages(store: ReminderStore, now: datetime) -> list[str]:
    return [f"⏰ Lembrete: {reminder.message}" for reminder in store.deliver_due(now)]


def main() -> None:
    for line in due_messages(ReminderStore(), datetime.now()):
        print(line)
