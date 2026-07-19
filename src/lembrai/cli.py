import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from groq import APIError, Groq

from lembrai import observability
from lembrai.agent import run_agent_turn
from lembrai.chat import MODEL
from lembrai.check import due_messages
from lembrai.cost import (
    SessionStats,
    Usage,
    combined_usage,
    format_session_stats,
    format_usage_line,
)
from lembrai.embeddings import create_embedder
from lembrai.history import Message, trimmed
from lembrai.notes import NoteMatch, NoteStore, as_context
from lembrai.onboarding import ask_profile, save_profile
from lembrai.profile import PROFILE_PATH, build_system_prompt, load_profile
from lembrai.reminders import ReminderStore
from lembrai.tools import Toolbox

BANNER = (
    "lembrai — seu assistente pessoal. "
    "Comandos: /nota <texto>, /stats, /limpar, /sair"
)
NOTE_USAGE_HINT = "uso: /nota <texto da nota>"


def dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def create_client() -> Groq:
    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY não encontrada — crie um arquivo .env (veja o README).")
    return Groq(api_key=api_key)


def offer_onboarding() -> str | None:
    question = "Você ainda não tem um Perfil. Quer fazer o onboarding agora? (s/n) "
    try:
        wants_onboarding = input(question).strip().lower() in {"s", "sim"}
        if not wants_onboarding:
            return None
        content = ask_profile()
    except (EOFError, KeyboardInterrupt):
        print(dim("\nonboarding cancelado — nenhum Perfil salvo"))
        return None
    if content is None:
        print(dim("nenhuma resposta preenchida — Perfil não criado"))
        return None
    save_profile(content)
    print(dim(f"Perfil salvo em {PROFILE_PATH} — edite o arquivo quando quiser."))
    return content


def respond(
    client: Groq,
    system_prompt: str,
    history: list[Message],
    note_matches: list[NoteMatch],
    toolbox: Toolbox,
) -> tuple[str | None, Usage | None]:
    messages: list[Message] = [{"role": "system", "content": system_prompt}]
    if note_matches:
        messages.append({"role": "system", "content": as_context(note_matches)})
    messages.extend(trimmed(history))
    print("\nlembrai › ", end="", flush=True)
    printed_any_chunk = False
    executed_tools = 0

    def print_chunk(text: str) -> None:
        nonlocal printed_any_chunk
        printed_any_chunk = True
        print(text, end="", flush=True)

    def print_tool(name: str, arguments: dict[str, object]) -> None:
        nonlocal executed_tools
        executed_tools += 1
        rendered = ", ".join(f"{key}={value!r}" for key, value in arguments.items())
        print(dim(f"\n[ferramenta: {name}({rendered})]"), flush=True)

    def print_malformed_tool(name: str) -> None:
        print(
            dim(f"\n[ferramenta: {name} — argumentos malformados, pedindo correção]"),
            flush=True,
        )

    def warn_kept_actions() -> None:
        # discarding the turn does not undo tools that already ran
        if executed_tools:
            print(
                dim(
                    f"[atenção: {executed_tools} ação(ões) de ferramenta "
                    "já executada(s) foram mantidas]"
                )
            )

    try:
        reply_text, usages = run_agent_turn(
            client,
            messages,
            toolbox,
            on_chunk=print_chunk,
            on_tool=print_tool,
            on_malformed_tool=print_malformed_tool,
        )
    except KeyboardInterrupt:
        print(dim("\n[resposta interrompida — turno descartado]"))
        warn_kept_actions()
        return None, None
    except APIError as error:
        partial_note = "resposta parcial descartada — " if printed_any_chunk else ""
        print(dim(f"\n[erro na API: {partial_note}{error.message}]"))
        warn_kept_actions()
        return None, None
    turn_usage = combined_usage(usages)
    if reply_text is None:
        print(dim("\n[limite de rodadas de ferramenta atingido — turno descartado]"))
        warn_kept_actions()
        return None, turn_usage
    print()
    return reply_text, turn_usage


def run_repl(
    client: Groq, system_prompt: str, store: NoteStore, toolbox: Toolbox
) -> SessionStats:
    history: list[Message] = []
    stats = SessionStats()
    while True:
        try:
            user_input = input("\nvocê › ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input == "/sair":
            break
        if user_input == "/limpar":
            history.clear()
            print(dim("histórico limpo"))
            continue
        if user_input == "/stats":
            print(dim(format_session_stats(MODEL, stats)))
            continue
        is_note_command = user_input == "/nota" or user_input.startswith("/nota ")
        if is_note_command:
            note_text = user_input.removeprefix("/nota").strip()
            if not note_text:
                print(dim(NOTE_USAGE_HINT))
                continue
            saved_path = store.add(note_text)
            print(dim(f"nota salva em {saved_path}"))
            continue
        history.append({"role": "user", "content": user_input})
        note_matches = store.search(user_input)
        reply, usage = respond(
            client, system_prompt, history, note_matches, toolbox
        )
        if reply is None:
            # failed or interrupted turn: drop the user message so history
            # matches what the model will actually see next turn, but keep
            # the tokens it cost
            stats.add_usage(usage)
            history.pop()
            continue
        history.append({"role": "assistant", "content": reply})
        stats.add_reply(usage)
        observability.record_turn(user_input, reply, MODEL, usage)
        if usage is not None:
            print(dim(f"· {format_usage_line(MODEL, usage)}"))
    return stats


def deliver_due_reminders() -> None:
    for line in due_messages(ReminderStore(), datetime.now()):
        print(dim(line))


def main() -> None:
    client = create_client()
    profile = load_profile()
    print(BANNER)
    deliver_due_reminders()
    if profile is None:
        profile = offer_onboarding()
    print(dim("carregando índice de Notas (modelo de embeddings)..."))
    store = NoteStore(embedder=create_embedder())
    stats = run_repl(client, build_system_prompt(profile), store, Toolbox())
    if stats.replies:
        print(dim(f"\nsessão: {format_session_stats(MODEL, stats)}"))
    observability.flush()
