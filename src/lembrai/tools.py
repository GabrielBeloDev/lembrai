import inspect
import json
from datetime import datetime
from pathlib import Path

from lembrai.reminders import REMINDERS_PATH, ReminderStore

CALENDAR_PATH = Path("data/calendar.json")
OUTBOX_DIR = Path("data/outbox")

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Cria um evento na agenda do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título do evento"},
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD",
                    },
                    "time": {
                        "type": "string",
                        "description": "Hora no formato HH:MM (opcional)",
                    },
                },
                "required": ["title", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "Lista todos os eventos da agenda do usuário.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Escreve um e-mail na caixa de saída local do usuário "
                "(o envio real ainda não está configurado)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Destinatário"},
                    "subject": {"type": "string", "description": "Assunto"},
                    "body": {"type": "string", "description": "Corpo do e-mail"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": (
                "Cria um lembrete que será entregue ao usuário na data e hora "
                "indicadas, sem ele precisar pedir de novo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "O que lembrar o usuário",
                    },
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD",
                    },
                    "time": {
                        "type": "string",
                        "description": "Hora no formato HH:MM (opcional, padrão 09:00)",
                    },
                },
                "required": ["message", "date"],
            },
        },
    },
]


class Toolbox:
    def __init__(
        self,
        calendar_path: Path = CALENDAR_PATH,
        outbox_dir: Path = OUTBOX_DIR,
        reminders_path: Path = REMINDERS_PATH,
    ):
        self._calendar_path = calendar_path
        self._outbox_dir = outbox_dir
        self._reminders = ReminderStore(reminders_path)

    def _load_events(self) -> list[dict[str, str | None]]:
        if not self._calendar_path.exists():
            return []
        return json.loads(self._calendar_path.read_text(encoding="utf-8"))

    def create_event(self, title: str, date: str, time: str | None = None) -> str:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            if time is not None:
                datetime.strptime(time, "%H:%M")
        except (TypeError, ValueError):
            # feed the format error back so the model can retry with valid values
            return "Data ou hora em formato inválido: use YYYY-MM-DD e HH:MM."
        events = self._load_events()
        events.append({"title": title, "date": date, "time": time})
        events.sort(key=lambda event: (event["date"], event["time"] or ""))
        self._calendar_path.parent.mkdir(parents=True, exist_ok=True)
        self._calendar_path.write_text(
            json.dumps(events, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        when = f"{date} às {time}" if time else date
        return f"Evento criado: {title} em {when}."

    def list_events(self) -> str:
        events = self._load_events()
        if not events:
            return "A agenda está vazia."
        lines = [_format_event_line(event) for event in events]
        return "Eventos na agenda:\n" + "\n".join(lines)

    def send_email(self, to: str, subject: str, body: str) -> str:
        self._outbox_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = self._outbox_dir / f"{stamp}.txt"
        path.write_text(
            f"Para: {to}\nAssunto: {subject}\n\n{body}\n", encoding="utf-8"
        )
        return f"E-mail para {to} salvo na caixa de saída local ({path})."

    def create_reminder(
        self, message: str, date: str, time: str | None = None
    ) -> str:
        clock = time or "09:00"
        try:
            due = datetime.strptime(f"{date} {clock}", "%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            return "Data ou hora em formato inválido: use YYYY-MM-DD e HH:MM."
        self._reminders.add(message, due)
        return f"Lembrete criado para {date} às {clock}: {message}"

    def execute(self, name: str, arguments: dict[str, object]) -> str:
        handlers = {
            "create_event": self.create_event,
            "list_events": self.list_events,
            "send_email": self.send_email,
            "create_reminder": self.create_reminder,
        }
        handler = handlers.get(name)
        if handler is None:
            return f"Ferramenta desconhecida: {name}."
        try:
            # bind() rejects hallucinated argument names with feedback to the
            # model, without masking genuine TypeErrors raised inside the handler
            bound = inspect.signature(handler).bind(**arguments)
        except TypeError as error:
            return f"Argumentos inválidos para {name}: {error}"
        return handler(*bound.args, **bound.kwargs)


def _format_event_line(event: dict[str, str | None]) -> str:
    when = f"{event['date']} {event['time']}" if event["time"] else event["date"]
    return f"- {when}: {event['title']}"
